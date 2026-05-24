import os
import re
from typing import List, Dict, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.observability.logging import logger
from app.rag.embeddings import embedding_engine
from llama_index.core.schema import TextNode

def tokenize_text(text: str) -> List[str]:
    if not text:
        return []
    return re.findall(r'\b\w+\b', text.lower())

class HybridRetrieverEngine:
    """
    Advanced Hybrid Retriever using Qdrant for both Dense and Sparse retrieval.
    Replaces the previous pickle-based BM25 with native Qdrant Sparse Vectors (if available)
    or a more robust in-memory sparse implementation.
    """
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self._init_qdrant_client()

    def _init_qdrant_client(self):
        logger.info(f"Initializing Qdrant client with mode: {settings.QDRANT_MODE}")
        if settings.QDRANT_MODE == "local":
            storage_path = os.path.join(settings.PROCESSED_DIR, "qdrant_storage")
            os.makedirs(storage_path, exist_ok=True)
            self.qdrant_client = QdrantClient(path=storage_path)
        else:
            if settings.QDRANT_URL:
                self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            else:
                self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

        self._ensure_collection()

    def _ensure_collection(self):
        dummy_vector = embedding_engine.get_embedding("test")
        vector_dim = len(dummy_vector)
        
        try:
            collections = self.qdrant_client.get_collections()
            exist = any(c.name == self.collection_name for c in collections.collections)
            if not exist:
                # In standard Qdrant, we use 'sparse_vectors_config' for native BM25/SPLADE.
                # Here we stick to a clean dense config but prepare for hybrid via RRF.
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE)
                )
                # Create Full-Text Index for Native Sparse Search
                from qdrant_client.models import TextIndexParams, TokenizerType
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="text",
                    field_schema=TextIndexParams(
                        type="text",
                        tokenizer=TokenizerType.WORD,
                        min_token_len=2,
                        max_token_len=20,
                        lowercase=True
                    )
                )
                logger.info(f"Created Qdrant collection and text index: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to verify or create Qdrant collection: {str(e)}")

    def save_nodes(self, nodes: List[TextNode]):
        if not nodes: return
        logger.info(f"Upserting {len(nodes)} nodes to Qdrant...")
        
        points = []
        for node in nodes:
            vector = embedding_engine.get_embedding(node.text)
            points.append(
                PointStruct(
                    id=node.node_id,
                    vector=vector,
                    payload={"text": node.text, **node.metadata}
                )
            )
            
        chunk_size = 100
        for i in range(0, len(points), chunk_size):
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points[i:i + chunk_size]
            )

    def retrieve_dense(self, query: str, top_k: int = 8, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        query_vector = embedding_engine.get_query_embedding(query)
        
        q_filter = None
        if metadata_filter:
            must = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in metadata_filter.items()]
            q_filter = Filter(must=must)

        try:
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=q_filter,
                limit=top_k
            )
            return [
                {
                    "id": res.id,
                    "text": res.payload.get("text", ""),
                    "metadata": {k: v for k, v in res.payload.items() if k != "text"},
                    "score": res.score,
                    "type": "dense"
                } for res in results
            ]
        except Exception as e:
            logger.error(f"Dense search error: {str(e)}")
            return []

    def retrieve_sparse(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        """
        Native Sparse Search (Mocking BM25 behavior via Qdrant Full-text search).
        Professional systems use Qdrant's internal Full-Text index.
        """
        try:
            # Using Qdrant's scroll with a filter acts as a keyword match search
            # if we have set up the payload indexes correctly.
            # For this MVP, we simulate sparse via full-text match.
            from qdrant_client.models import Filter, FieldCondition, MatchText
            
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    should=[FieldCondition(key="text", match=MatchText(text=query))]
                ),
                limit=top_k,
                with_payload=True
            )[0]
            
            return [
                {
                    "id": res.id,
                    "text": res.payload.get("text", ""),
                    "metadata": {k: v for k, v in res.payload.items() if k != "text"},
                    "score": 0.5, # Mock score for full-text scroll
                    "type": "sparse"
                } for res in results
            ]
        except Exception as e:
            logger.error(f"Sparse search error: {str(e)}")
            return []

    def delete_document(self, doc_id: str):
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                )
            )
        except Exception as e:
            logger.error(f"Deletion error: {str(e)}")

    @property
    def bm25_nodes(self) -> List[Dict[str, Any]]:
        """
        Dynamically fetches all documents in the collection to act as the in-memory node store
        for backwards-compatibility with MCP resources and tools.
        """
        try:
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )[0]
            return [
                {
                    "id": res.id,
                    "text": res.payload.get("text", ""),
                    "metadata": {k: v for k, v in res.payload.items() if k != "text"}
                } for res in results
            ]
        except Exception as e:
            logger.error(f"Error scrolling bm25_nodes from Qdrant: {str(e)}")
            return []

    def get_all_document_ids(self) -> List[str]:
        try:
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )[0]
            doc_ids = set()
            for res in results:
                doc_id = res.payload.get("doc_id")
                if doc_id:
                    doc_ids.add(doc_id)
            return list(doc_ids)
        except Exception as e:
            logger.error(f"Error getting document ids from Qdrant: {str(e)}")
            return []

    def get_document_nodes(self, doc_id: str) -> List[Dict[str, Any]]:
        try:
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                ),
                limit=10000,
                with_payload=True,
                with_vectors=False
            )[0]
            return [
                {
                    "id": res.id,
                    "text": res.payload.get("text", ""),
                    "metadata": {k: v for k, v in res.payload.items() if k != "text"}
                } for res in results
            ]
        except Exception as e:
            logger.error(f"Error getting document nodes from Qdrant: {str(e)}")
            return []

hybrid_retriever_engine = HybridRetrieverEngine()
