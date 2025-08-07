import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import uuid
import logging
from models import Product
from core.config import settings
from core.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = None
        self.embedding_service = EmbeddingService()
        self._initialize_collection()
    
    def _initialize_collection(self):
        try:
            self.collection = self.client.get_or_create_collection(
                name="products",
                metadata={"description": "Product catalog embeddings"}
            )
            logger.info(f"Initialized vector store with {self.collection.count()} items")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
    
    async def add_product(self, product: Product) -> bool:
        try:
            search_text = product.to_search_text()
            embedding = await self.embedding_service.create_embedding(search_text)
            
            metadata = {
                "product_id": product.product_id,
                "name": product.name,
                "category": product.category.value,
                "price": product.get_display_price(),
                "brand": product.attributes.brand or "",
                "colors": ",".join(product.attributes.color) if product.attributes.color else "",
                "occasions": ",".join([o.value for o in product.attributes.occasion]) if product.attributes.occasion else "",
                "seasons": ",".join([s.value for s in product.attributes.season]) if product.attributes.season else "",
                "in_stock": product.in_stock
            }
            
            self.collection.add(
                ids=[product.product_id],
                embeddings=[embedding],
                documents=[search_text],
                metadatas=[metadata]
            )
            
            return True
        except Exception as e:
            logger.error(f"Error adding product to vector store: {e}")
            return False
    
    async def add_products_batch(self, products: List[Product]) -> int:
        try:
            texts = [p.to_search_text() for p in products]
            embeddings = await self.embedding_service.create_batch_embeddings(texts)
            
            ids = []
            metadatas = []
            documents = []
            valid_embeddings = []
            
            for i, product in enumerate(products):
                ids.append(product.product_id)
                documents.append(texts[i])
                valid_embeddings.append(embeddings[i])
                
                metadata = {
                    "product_id": product.product_id,
                    "name": product.name,
                    "category": product.category.value,
                    "price": product.get_display_price(),
                    "brand": product.attributes.brand or "",
                    "colors": ",".join(product.attributes.color) if product.attributes.color else "",
                    "occasions": ",".join([o.value for o in product.attributes.occasion]) if product.attributes.occasion else "",
                    "seasons": ",".join([s.value for s in product.attributes.season]) if product.attributes.season else "",
                    "in_stock": product.in_stock
                }
                metadatas.append(metadata)
            
            self.collection.add(
                ids=ids,
                embeddings=valid_embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            return len(ids)
        except Exception as e:
            logger.error(f"Error adding products batch: {e}")
            return 0
    
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = await self.embedding_service.create_embedding(query)
            
            where_clause = {}
            if filters:
                if "category" in filters and filters["category"]:
                    where_clause["category"] = {"$in": filters["category"]}
                if "max_price" in filters and filters["max_price"]:
                    where_clause["price"] = {"$lte": filters["max_price"]}
                if "in_stock" in filters:
                    where_clause["in_stock"] = filters["in_stock"]
                if "brand" in filters and filters["brand"]:
                    where_clause["brand"] = {"$in": filters["brand"]}
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count()),
                where=where_clause if where_clause else None,
                include=["metadatas", "distances", "documents"]
            )
            
            formatted_results = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "product_id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                        "document": results["documents"][0][i] if results["documents"] else ""
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    async def get_similar_products(self, product_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        try:
            product_data = self.collection.get(ids=[product_id], include=["embeddings", "documents"])
            
            if not product_data["embeddings"]:
                return []
            
            embedding = product_data["embeddings"][0]
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k + 1,
                include=["metadatas", "distances", "documents"]
            )
            
            formatted_results = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    if results["ids"][0][i] != product_id:
                        formatted_results.append({
                            "product_id": results["ids"][0][i],
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else 0,
                            "document": results["documents"][0][i] if results["documents"] else ""
                        })
            
            return formatted_results[:top_k]
        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return []
    
    def delete_product(self, product_id: str) -> bool:
        try:
            self.collection.delete(ids=[product_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False
    
    def clear_all(self) -> bool:
        try:
            self.client.delete_collection("products")
            self._initialize_collection()
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False