import numpy as np
from typing import List, Optional, Dict, Any
import openai
from sentence_transformers import SentenceTransformer
import logging
from tizzl.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.openai_client = None
        self.sentence_transformer = None
        self.model_type = "openai"
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            self.model_type = "openai"
        else:
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            self.model_type = "sentence_transformer"
            logger.info("Using Sentence Transformers for embeddings")
    
    async def create_embedding(self, text: str) -> List[float]:
        try:
            if self.model_type == "openai" and self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=settings.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            else:
                embedding = self.sentence_transformer.encode(text, convert_to_numpy=True)
                return embedding.tolist()
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return self._get_random_embedding()
    
    async def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            if self.model_type == "openai" and self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=settings.embedding_model,
                    input=texts
                )
                return [item.embedding for item in response.data]
            else:
                embeddings = self.sentence_transformer.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {e}")
            return [self._get_random_embedding() for _ in texts]
    
    def _get_random_embedding(self) -> List[float]:
        dimension = 1536 if self.model_type == "openai" else 384
        return np.random.randn(dimension).tolist()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    @staticmethod
    def combine_embeddings(embeddings: List[List[float]], weights: Optional[List[float]] = None) -> List[float]:
        if not embeddings:
            return []
        
        embeddings_array = np.array(embeddings)
        
        if weights:
            weights_array = np.array(weights).reshape(-1, 1)
            weighted_sum = np.sum(embeddings_array * weights_array, axis=0)
            combined = weighted_sum / np.sum(weights)
        else:
            combined = np.mean(embeddings_array, axis=0)
        
        combined_normalized = combined / np.linalg.norm(combined)
        return combined_normalized.tolist()