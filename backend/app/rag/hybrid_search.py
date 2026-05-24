from typing import List, Dict, Any
from app.rag.retriever import hybrid_retriever_engine
from app.config import settings
from app.observability.logging import logger

class HybridSearchEngine:
    def __init__(self, alpha: float = None, rrf_k: int = 60):
        self.alpha = alpha if alpha is not None else settings.HYBRID_ALPHA
        self.rrf_k = rrf_k  # RRF constant, usually 60

    def rrf_merge(self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]], top_k: int = 8) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm.
        RRF scores are calculated by: 
        RRF(doc) = sum_{m in models} 1 / (k + rank_m(doc))
        This is a robust and parameter-free technique to combine lists with different score scales.
        """
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}
        
        # Rank mapping for dense
        for rank, doc in enumerate(dense_results):
            doc_id = doc["id"]
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))
            
        # Rank mapping for sparse
        for rank, doc in enumerate(sparse_results):
            doc_id = doc["id"]
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))
            
        # Sort docs based on RRF scores
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        merged_results = []
        for doc_id, score in sorted_docs[:top_k]:
            orig_doc = doc_map[doc_id]
            merged_results.append({
                "id": doc_id,
                "text": orig_doc["text"],
                "metadata": orig_doc["metadata"],
                "score": score,
                "dense_score": next((d["score"] for d in dense_results if d["id"] == doc_id), None),
                "sparse_score": next((s["score"] for s in sparse_results if s["id"] == doc_id), None)
            })
            
        return merged_results

    def search(self, query: str, top_k: int = None, use_reranker: bool = False, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        top_k = top_k or settings.TOP_K
        logger.info(f"Initiating hybrid search for query: '{query}' with top_k: {top_k}, filter: {metadata_filter}")
        
        # Fetch both lists
        dense_res = hybrid_retriever_engine.retrieve_dense(query, top_k=top_k * 2, metadata_filter=metadata_filter)
        sparse_res = hybrid_retriever_engine.retrieve_sparse(query, top_k=top_k * 2)
        
        # Filter sparse results manually for now if filter is provided
        if metadata_filter and sparse_res:
            filtered_sparse = []
            for doc in sparse_res:
                match = True
                for key, value in metadata_filter.items():
                    if doc.get("metadata", {}).get(key) != value:
                        match = False
                        break
                if match:
                    filtered_sparse.append(doc)
            sparse_res = filtered_sparse

        logger.debug(f"Dense search retrieved {len(dense_res)} docs, Sparse search retrieved {len(sparse_res)} docs")
        
        # Merge lists
        merged_res = self.rrf_merge(dense_res, sparse_res, top_k=top_k)
        
        # Optionally rerank
        if use_reranker or settings.USE_RERANKER:
            from app.rag.reranker import reranker_engine
            merged_res = reranker_engine.rerank(query, merged_res, top_k=top_k)
            
        logger.info(f"Hybrid search completed. Top score: {merged_res[0]['score'] if merged_res else 'N/A'}")
        return merged_res

hybrid_search_engine = HybridSearchEngine()
