import uuid
import time
import logging
import asyncio
from typing import List, Optional, Dict, Any
from models import (
    Product, UserProfile, UserQuery, 
    StylistResponse, OutfitRecommendation, OutfitItem
)
from services.retrieval_service import RetrievalService
from services.unified_llm_service import UnifiedLLMService
from services.query_router import QueryRouter, QueryType
from services.cache_service import CacheService
from core.vector_store import VectorStore
from core.config import settings

logger = logging.getLogger(__name__)

class OptimizedStylistService:
    """
    Optimized stylist service with:
    - Query routing for greetings/non-styling queries
    - Single unified LLM call
    - Caching for improved performance
    - Parallel processing where possible
    """
    
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.unified_llm = UnifiedLLMService()
        self.cache_service = CacheService()
        self.vector_store = VectorStore()
    
    async def process_query(
        self,
        query: UserQuery,
        user_profile: Optional[UserProfile] = None
    ) -> StylistResponse:
        """
        Main entry point for processing queries with optimizations
        """
        start_time = time.time()
        response_id = str(uuid.uuid4())
        
        logger.info(f"[{response_id}] Processing query: '{query.query}'")
        
        # Step 1: Route query to determine type
        routing_result = QueryRouter.route_query(query.query)
        query_type = routing_result['type']
        
        logger.info(f"[{response_id}] Query type: {query_type}, confidence: {routing_result['confidence']:.2f}")
        
        # Step 2: Handle non-styling queries immediately
        if routing_result['skip_processing']:
            processing_time = int((time.time() - start_time) * 1000)
            return StylistResponse(
                response_id=response_id,
                user_query=query.query,
                recommendations=[],
                styling_advice=routing_result['response'],
                processing_time_ms=processing_time
            )
        
        # Step 3: Check cache for styling queries
        cache_key = None
        if self.cache_service.enabled:
            cached_result = await self.cache_service.get_query_result(
                query.query, 
                user_profile.user_id if user_profile else None
            )
            if cached_result:
                logger.info(f"[{response_id}] Cache hit - returning cached response")
                cached_result['response_id'] = response_id
                cached_result['processing_time_ms'] = int((time.time() - start_time) * 1000)
                return StylistResponse(**cached_result)
        
        # Step 4: Process styling query with optimizations
        try:
            # Run vector search and initial processing in parallel
            search_task = asyncio.create_task(
                self._optimized_product_search(query, user_profile)
            )
            
            # Get products from search
            products = await search_task
            
            if not products:
                logger.warning(f"[{response_id}] No products found")
                return self._create_empty_response(query.query, "No matching products found")
            
            logger.info(f"[{response_id}] Retrieved {len(products)} products")
            
            # Step 5: Single unified LLM call for all operations
            llm_result = await self.unified_llm.process_styling_query(
                query.query,
                products,
                user_profile,
                {'occasion': query.occasion} if query.occasion else None
            )
            
            # Step 6: Parse and create response
            response = await self._create_optimized_response(
                response_id,
                query.query,
                llm_result,
                products,
                user_profile,
                start_time
            )
            
            # Step 7: Cache the result
            if self.cache_service.enabled:
                await self.cache_service.set_query_result(
                    query.query,
                    response.dict(),
                    user_profile.user_id if user_profile else None
                )
            
            return response
            
        except Exception as e:
            logger.error(f"[{response_id}] Error processing query: {e}", exc_info=True)
            return self._create_error_response(query.query, str(e))
    
    async def _optimized_product_search(
        self,
        query: UserQuery,
        user_profile: Optional[UserProfile] = None
    ) -> List[Product]:
        """
        Optimized product search with caching and reduced scope
        """
        try:
            # Build filters efficiently
            filters = self._build_optimized_filters(query, user_profile)
            
            # Limit initial search for better performance
            search_results = await self.vector_store.search(
                query=query.query,
                filters=filters,
                top_k=min(30, settings.rerank_top_k)  # Reduced from 50
            )
            
            # Load products efficiently
            products = await self._load_products_batch(search_results)
            
            # Apply business rules
            products = self._apply_business_rules(products, query)
            
            return products[:settings.final_top_k]
            
        except Exception as e:
            logger.error(f"Error in optimized product search: {e}")
            return []
    
    def _build_optimized_filters(
        self, 
        query: UserQuery, 
        user_profile: Optional[UserProfile]
    ) -> Dict[str, Any]:
        """Build optimized filters for vector search"""
        filters = {"in_stock": True}
        
        if query.preferred_categories:
            filters["category"] = query.preferred_categories
        
        if query.budget:
            filters["max_price"] = query.budget
        elif user_profile and user_profile.budget_max:
            filters["max_price"] = user_profile.budget_max
        
        if not query.include_sale_items:
            filters["on_sale"] = False
        
        return filters
    
    async def _load_products_batch(self, search_results: List[Dict[str, Any]]) -> List[Product]:
        """Load products efficiently with batching"""
        products = []
        
        for result in search_results:
            product_id = result.get("product_id")
            metadata = result.get("metadata", {})
            
            # Create product from metadata (avoid additional DB calls)
            product = self._create_product_from_metadata(product_id, metadata)
            if product:
                products.append(product)
        
        return products
    
    def _create_product_from_metadata(self, product_id: str, metadata: Dict[str, Any]) -> Optional[Product]:
        """Create product object from metadata efficiently"""
        from models import Category, Occasion, Season, ProductAttribute
        
        try:
            attributes = ProductAttribute(
                color=metadata.get("colors", "").split(",") if metadata.get("colors") else [],
                brand=metadata.get("brand"),
                occasion=[Occasion(o) for o in metadata.get("occasions", "").split(",") if o] if metadata.get("occasions") else [],
                season=[Season(s) for s in metadata.get("seasons", "").split(",") if s] if metadata.get("seasons") else []
            )
            
            return Product(
                product_id=product_id,
                name=metadata.get("name", f"Product {product_id}"),
                category=Category(metadata.get("category", "tops")),
                description=metadata.get("description", "Fashion item"),
                attributes=attributes,
                price=metadata.get("price", 99.99),
                in_stock=metadata.get("in_stock", True)
            )
        except Exception as e:
            logger.error(f"Error creating product from metadata: {e}")
            return None
    
    def _apply_business_rules(self, products: List[Product], query: UserQuery) -> List[Product]:
        """Apply business rules efficiently"""
        if not query.excluded_categories and not query.budget and not query.color_preferences:
            return products  # Skip if no filters to apply
        
        filtered = []
        for product in products:
            # Exclusion checks
            if query.excluded_categories and product.category.value in query.excluded_categories:
                continue
            
            if query.budget and product.get_display_price() > query.budget:
                continue
            
            # Color preference check
            if query.color_preferences and product.attributes.color:
                if not any(color in product.attributes.color for color in query.color_preferences):
                    continue
            
            filtered.append(product)
        
        return filtered
    
    async def _create_optimized_response(
        self,
        response_id: str,
        query: str,
        llm_result: Dict[str, Any],
        products: List[Product],
        user_profile: Optional[UserProfile],
        start_time: float
    ) -> StylistResponse:
        """Create optimized response from unified LLM result"""
        
        # Convert LLM result to outfit recommendations
        outfits = []
        for outfit_data in llm_result.get('outfits', []):
            outfit_items = []
            
            for product in outfit_data.get('products', []):
                outfit_item = OutfitItem(
                    product=product,
                    styling_notes=", ".join(outfit_data.get('styling_tips', [])),
                    role_in_outfit=self._determine_role(product.category.value)
                )
                outfit_items.append(outfit_item)
            
            if outfit_items:
                outfit = OutfitRecommendation(
                    outfit_id=str(uuid.uuid4()),
                    name=outfit_data.get('name', 'Outfit'),
                    description=outfit_data.get('description', ''),
                    items=outfit_items,
                    total_price=outfit_data.get('total_price', 0),
                    styling_tips=outfit_data.get('styling_tips', []),
                    confidence_score=0.85
                )
                outfits.append(outfit)
        
        # Get top ranked products for individual items
        ranked_products = llm_result.get('ranked_products', [])
        individual_items = [item['product'] for item in ranked_products[:5]]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return StylistResponse(
            response_id=response_id,
            user_query=query,
            recommendations=outfits,
            individual_items=individual_items,
            styling_advice=llm_result.get('styling_advice', ''),
            personalization_notes=self._generate_personalization_notes(user_profile),
            processing_time_ms=processing_time
        )
    
    def _determine_role(self, category: str) -> str:
        """Determine role of item in outfit"""
        role_map = {
            "tops": "Top",
            "bottoms": "Bottom",
            "dresses": "Main Piece",
            "outerwear": "Layer",
            "shoes": "Footwear",
            "accessories": "Accent",
            "bags": "Bag",
            "jewelry": "Jewelry"
        }
        return role_map.get(category, "Item")
    
    def _generate_personalization_notes(self, profile: Optional[UserProfile]) -> Optional[str]:
        """Generate personalization notes"""
        if not profile:
            return None
        
        notes = []
        
        if profile.body_type:
            notes.append(f"Tailored for {profile.body_type.value} body type")
        
        if profile.style_preferences and profile.style_preferences.style_personalities:
            styles = ", ".join([s.value for s in profile.style_preferences.style_personalities])
            notes.append(f"Matches your {styles} style")
        
        if profile.budget_max:
            notes.append(f"Within ${profile.budget_max:.0f} budget")
        
        return ". ".join(notes) if notes else None
    
    def _create_empty_response(self, query: str, message: str) -> StylistResponse:
        """Create empty response"""
        return StylistResponse(
            response_id=str(uuid.uuid4()),
            user_query=query,
            recommendations=[],
            styling_advice=message
        )
    
    def _create_error_response(self, query: str, error: str) -> StylistResponse:
        """Create error response"""
        return StylistResponse(
            response_id=str(uuid.uuid4()),
            user_query=query,
            recommendations=[],
            styling_advice="I encountered an issue processing your request. Please try again."
        )
    
    async def get_style_advice(
        self,
        query: str,
        user_profile: Optional[UserProfile] = None
    ) -> str:
        """Get simple style advice without product search"""
        
        # Check if it's a greeting or non-styling query
        routing_result = QueryRouter.route_query(query)
        if routing_result['skip_processing']:
            return routing_result['response']
        
        # Generate style advice
        return await self.unified_llm.generate_simple_advice(query)