from typing import List, Dict, Any
from app.observability.logging import logger
from app.config import settings
import numpy as np

class RerankerEngine:
    def __init__(self):
        self.model = None
        # Use settings to decide if we should load the model
        if getattr(settings, "USE_RERANKER", False):
            try:
                from sentence_transformers import CrossEncoder
                # Use a lightweight but effective cross-encoder
                self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
                logger.info("Successfully loaded Cross-Encoder reranker model.")
            except Exception as e:
                logger.error(f"Failed to load Cross-Encoder: {str(e)}. Falling back to cosine similarity.")

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 8) -> List[Dict[str, Any]]:
        if not documents:
            return []
            
        logger.info(f"Rerank requested. Processing {len(documents)} documents using {'Cross-Encoder' if self.model else 'Cosine Similarity'}...")
        
        try:
            if self.model:
                # 1. Prepare pairs for Cross-Encoder
                pairs = [[query, doc["text"]] for doc in documents]
                
                # 2. Predict scores
                scores = self.model.predict(pairs)
                
                scored_docs = []
                for idx, doc in enumerate(documents):
                    doc_copy = doc.copy()
                    doc_copy["rerank_score"] = float(scores[idx])
                    doc_copy["score"] = float(scores[idx]) 
                    scored_docs.append(doc_copy)
            else:
                # Fallback to cosine similarity if model not loaded
                from app.rag.embeddings import embedding_engine
                query_vec = np.array(embedding_engine.get_query_embedding(query))
                scored_docs = []
                for doc in documents:
                    doc_vec = np.array(embedding_engine.get_embedding(doc["text"]))
                    # Avoid division by zero
                    norm_q = np.linalg.norm(query_vec)
                    norm_d = np.linalg.norm(doc_vec)
                    if norm_q > 0 and norm_d > 0:
                        cosine_sim = np.dot(query_vec, doc_vec) / (norm_q * norm_d)
                    else:
                        cosine_sim = 0.0
                        
                    doc_copy = doc.copy()
                    doc_copy["score"] = float(cosine_sim)
                    doc_copy["cosine_similarity"] = float(cosine_sim)
                    scored_docs.append(doc_copy)
                
            # Sort by score descending
            scored_docs.sort(key=lambda x: x["score"], reverse=True)
            logger.info(f"Reranking completed. Top score: {scored_docs[0]['score']}")
            return scored_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}", exc_info=True)
            return documents[:top_k]

reranker_engine = RerankerEngine()
