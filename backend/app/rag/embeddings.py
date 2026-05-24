from typing import List
from app.config import settings
from app.observability.logging import logger

class EmbeddingEngine:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self._client = None
        self._init_embedding_client()

    def _init_embedding_client(self):
        logger.info(f"Initializing embedding client using provider: {self.provider}")
        
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY is not set. Falling back to local HuggingFace embeddings.")
                self.provider = "local"
                self._init_local()
            else:
                from llama_index.embeddings.openai import OpenAIEmbedding
                self._client = OpenAIEmbedding(
                    model=settings.OPENAI_EMBED_MODEL,
                    api_key=settings.OPENAI_API_KEY
                )
                
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY is not set. Falling back to local HuggingFace embeddings.")
                self.provider = "local"
                self._init_local()
            else:
                from llama_index.embeddings.gemini import GeminiEmbedding
                self._client = GeminiEmbedding(
                    model_name=settings.GEMINI_EMBED_MODEL,
                    api_key=settings.GEMINI_API_KEY
                )
                
        elif self.provider == "ollama":
            from llama_index.embeddings.ollama import OllamaEmbedding
            self._client = OllamaEmbedding(
                model_name=settings.OLLAMA_EMBED_MODEL,
                base_url=settings.OLLAMA_BASE_URL
            )
            
        else:
            self.provider = "local"
            self._init_local()

    def _init_local(self):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        logger.info(f"Loading local HuggingFace embedding model: {settings.LOCAL_EMBEDDING_MODEL}")
        self._client = HuggingFaceEmbedding(
            model_name=settings.LOCAL_EMBEDDING_MODEL
        )

    def get_embedding(self, text: str) -> List[float]:
        return self._client.get_text_embedding(text)

    def get_query_embedding(self, query: str) -> List[float]:
        return self._client.get_query_embedding(query)

    async def aget_embedding(self, text: str) -> List[float]:
        return await self._client.aget_text_embedding(text)

embedding_engine = EmbeddingEngine()
