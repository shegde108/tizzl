from typing import List, Dict, Any, Optional
import logging
from ..core.vector_store import VectorStore
from ..core.embeddings import EmbeddingService
from ..models import Product, UserQuery
from .llm_service import LLMService
from ..core.config import settings

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.product_cache = {}
    
    async def retrieve_products(
        self,
        query: UserQuery,
        user_profile: Optional[Any] = None
    ) -> List[Product]:
        try:
            enhanced_terms = await self.llm_service.enhance_search_query(query.query)
            
            combined_query = f"{query.query} {' '.join(enhanced_terms)}"
            
            filters = self._build_filters(query)
            
            search_results = await self.vector_store.search(
                query=combined_query,
                filters=filters,
                top_k=settings.rerank_top_k
            )
            
            products = await self._load_products(search_results)
            
            if len(products) > settings.final_top_k:
                product_ids = await self.llm_service.rerank_products(query.query, products)
                products = self._reorder_products(products, product_ids)
                products = products[:settings.final_top_k]
            
            products = self._apply_business_rules(products, query)
            
            return products
        except Exception as e:
            logger.error(f"Error retrieving products: {e}")
            return []
    
    async def get_outfit_combinations(
        self,
        anchor_product: Product,
        query: Optional[UserQuery] = None
    ) -> List[List[Product]]:
        try:
            outfits = []
            
            complementary_categories = self._get_complementary_categories(anchor_product.category.value)
            
            for category in complementary_categories:
                filters = {
                    "category": [category],
                    "in_stock": True
                }
                
                if anchor_product.attributes.occasion:
                    search_query = f"match with {anchor_product.name} for {anchor_product.attributes.occasion[0].value}"
                else:
                    search_query = f"coordinate with {anchor_product.name}"
                
                results = await self.vector_store.search(
                    query=search_query,
                    filters=filters,
                    top_k=5
                )
                
                products = await self._load_products(results[:3])
                
                for product in products:
                    outfit = [anchor_product, product]
                    outfits.append(outfit)
            
            return outfits[:5]
        except Exception as e:
            logger.error(f"Error getting outfit combinations: {e}")
            return []
    
    async def find_similar_items(
        self,
        product_id: str,
        top_k: int = 10
    ) -> List[Product]:
        try:
            similar_results = await self.vector_store.get_similar_products(product_id, top_k)
            return await self._load_products(similar_results)
        except Exception as e:
            logger.error(f"Error finding similar items: {e}")
            return []
    
    def _build_filters(self, query: UserQuery) -> Dict[str, Any]:
        filters = {}
        
        if query.preferred_categories:
            filters["category"] = query.preferred_categories
        
        if query.budget:
            filters["max_price"] = query.budget
        
        if not query.include_sale_items:
            filters["on_sale"] = False
        
        filters["in_stock"] = True
        
        return filters
    
    async def _load_products(self, search_results: List[Dict[str, Any]]) -> List[Product]:
        products = []
        
        for result in search_results:
            product_id = result.get("product_id")
            
            if product_id in self.product_cache:
                products.append(self.product_cache[product_id])
            else:
                product = await self._fetch_product(product_id, result.get("metadata", {}))
                if product:
                    self.product_cache[product_id] = product
                    products.append(product)
        
        return products
    
    async def _fetch_product(self, product_id: str, metadata: Dict[str, Any]) -> Optional[Product]:
        from ..models import Category, Occasion, Season, ProductAttribute
        
        try:
            colors = metadata.get("colors", "").split(",") if metadata.get("colors") else []
            occasions = [Occasion(o) for o in metadata.get("occasions", "").split(",") if o] if metadata.get("occasions") else []
            seasons = [Season(s) for s in metadata.get("seasons", "").split(",") if s] if metadata.get("seasons") else []
            
            attributes = ProductAttribute(
                color=colors,
                brand=metadata.get("brand"),
                occasion=occasions,
                season=seasons
            )
            
            product = Product(
                product_id=product_id,
                name=metadata.get("name", f"Product {product_id}"),
                category=Category(metadata.get("category", "tops")),
                description=f"Fashion item - {metadata.get('name', 'Product')}",
                attributes=attributes,
                price=metadata.get("price", 99.99),
                in_stock=metadata.get("in_stock", True)
            )
            
            return product
        except Exception as e:
            logger.error(f"Error creating product from metadata: {e}")
            return None
    
    def _reorder_products(self, products: List[Product], ordered_ids: List[str]) -> List[Product]:
        product_map = {p.product_id: p for p in products}
        reordered = []
        
        for pid in ordered_ids:
            if pid in product_map:
                reordered.append(product_map[pid])
        
        for p in products:
            if p.product_id not in ordered_ids:
                reordered.append(p)
        
        return reordered
    
    def _apply_business_rules(self, products: List[Product], query: UserQuery) -> List[Product]:
        filtered = []
        
        for product in products:
            if query.excluded_categories and product.category.value in query.excluded_categories:
                continue
            
            if query.budget and product.get_display_price() > query.budget:
                continue
            
            if query.color_preferences:
                has_preferred_color = any(
                    color in product.attributes.color 
                    for color in query.color_preferences
                ) if product.attributes.color else False
                
                if query.color_preferences and not has_preferred_color:
                    continue
            
            filtered.append(product)
        
        return filtered
    
    def _get_complementary_categories(self, category: str) -> List[str]:
        category_map = {
            "tops": ["bottoms", "outerwear", "shoes", "accessories"],
            "bottoms": ["tops", "shoes", "outerwear", "accessories"],
            "dresses": ["outerwear", "shoes", "bags", "jewelry"],
            "outerwear": ["tops", "bottoms", "dresses", "accessories"],
            "shoes": ["tops", "bottoms", "dresses", "bags"],
            "accessories": ["tops", "bottoms", "dresses", "outerwear"],
            "bags": ["shoes", "jewelry", "accessories"],
            "jewelry": ["dresses", "tops", "bags"]
        }
        
        return category_map.get(category, ["tops", "bottoms", "accessories"])