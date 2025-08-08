from typing import List, Optional, Dict, Any
import uuid
import time
import logging
from models import (
    Product, UserProfile, UserQuery, 
    StylistResponse, OutfitRecommendation, OutfitItem
)
from services.retrieval_service import RetrievalService
from services.llm_service import LLMService
from core.config import settings

logger = logging.getLogger(__name__)

class StylistService:
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.llm_service = LLMService()
    
    async def get_styling_recommendations(
        self,
        query: UserQuery,
        user_profile: Optional[UserProfile] = None
    ) -> StylistResponse:
        start_time = time.time()
        response_id = str(uuid.uuid4())
        
        logger.info(f"[{response_id}] Starting stylist recommendation process")
        logger.info(f"[{response_id}] Query: '{query.query}', Context: {query.context}")
        logger.info(f"[{response_id}] User profile: {user_profile.model_dump() if user_profile else 'None'}")
        
        try:
            logger.info(f"[{response_id}] Step 1: Retrieving products from vector store")
            products = await self.retrieval_service.retrieve_products(query, user_profile)
            logger.info(f"[{response_id}] Retrieved {len(products)} products")
            
            if not products:
                logger.warning(f"[{response_id}] No products found, returning empty response")
                return self._create_empty_response(query.query, "No matching products found")
            
            # Log product details
            for i, product in enumerate(products[:5]):  # Log first 5 products
                logger.debug(f"[{response_id}] Product {i+1}: {product.name} ({product.category.value}) - ${product.get_display_price()}")
            
            logger.info(f"[{response_id}] Step 2: Generating LLM outfit recommendations")
            llm_response = await self.llm_service.generate_outfit_recommendations(
                query.query,
                products,
                user_profile,
                query.context
            )
            logger.info(f"[{response_id}] LLM response generated ({len(llm_response)} characters)")
            logger.debug(f"[{response_id}] LLM response preview: {llm_response[:200]}...")
            
            logger.info(f"[{response_id}] Step 3: Parsing outfit recommendations from LLM response")
            outfits = await self._parse_outfit_recommendations(llm_response, products)
            logger.info(f"[{response_id}] Parsed {len(outfits)} outfit recommendations")
            
            # Log outfit details
            for i, outfit in enumerate(outfits):
                logger.debug(f"[{response_id}] Outfit {i+1}: '{outfit.name}' with {len(outfit.items)} items, total: ${outfit.total_price:.2f}")
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"[{response_id}] Step 4: Creating final response")
            
            personalization_notes = self._generate_personalization_notes(user_profile)
            logger.debug(f"[{response_id}] Personalization notes: {personalization_notes}")
            
            response = StylistResponse(
                response_id=response_id,
                user_query=query.query,
                recommendations=outfits,
                individual_items=products[:5],
                styling_advice=llm_response,
                personalization_notes=personalization_notes,
                processing_time_ms=processing_time
            )
            
            logger.info(f"[{response_id}] Stylist recommendation process completed successfully in {processing_time}ms")
            return response
            
        except Exception as e:
            logger.error(f"[{response_id}] Error getting styling recommendations: {e}", exc_info=True)
            return self._create_error_response(query.query, str(e))
    
    async def get_outfit_for_product(
        self,
        product_id: str,
        user_profile: Optional[UserProfile] = None
    ) -> List[OutfitRecommendation]:
        logger.info(f"Getting outfit recommendations for product: {product_id}")
        try:
            product = await self._get_product_by_id(product_id)
            if not product:
                logger.warning(f"Product not found: {product_id}")
                return []
            
            logger.debug(f"Found product: {product.name} ({product.category.value})")
            outfit_combinations = await self.retrieval_service.get_outfit_combinations(product)
            logger.debug(f"Retrieved {len(outfit_combinations)} outfit combinations")
            
            outfits = []
            for i, combo in enumerate(outfit_combinations):
                logger.debug(f"Processing outfit combination {i+1} with {len(combo)} items")
                outfit = await self._create_outfit_from_products(combo, user_profile)
                if outfit:
                    outfits.append(outfit)
            
            logger.info(f"Created {len(outfits)} outfit recommendations for product {product_id}")
            return outfits
            
        except Exception as e:
            logger.error(f"Error getting outfit for product {product_id}: {e}", exc_info=True)
            return []
    
    async def get_similar_styles(
        self,
        product_id: str,
        top_k: int = 10
    ) -> List[Product]:
        logger.info(f"Finding {top_k} similar styles for product: {product_id}")
        try:
            similar_items = await self.retrieval_service.find_similar_items(product_id, top_k)
            logger.info(f"Found {len(similar_items)} similar items for product {product_id}")
            return similar_items
        except Exception as e:
            logger.error(f"Error getting similar styles for {product_id}: {e}", exc_info=True)
            return []
    
    async def get_style_advice(
        self,
        query: str,
        user_profile: Optional[UserProfile] = None
    ) -> str:
        logger.info(f"Generating style advice for query: '{query}'")
        logger.debug(f"User profile provided: {user_profile is not None}")
        try:
            advice = await self.llm_service.generate_style_advice(query, user_profile)
            logger.info(f"Generated style advice ({len(advice)} characters)")
            return advice
        except Exception as e:
            logger.error(f"Error getting style advice for query '{query}': {e}", exc_info=True)
            return "I'd be happy to help with your style question. Please try rephrasing or provide more details."
    
    async def _parse_outfit_recommendations(
        self,
        llm_response: str,
        available_products: List[Product]
    ) -> List[OutfitRecommendation]:
        logger.debug(f"Parsing outfit recommendations from LLM response")
        logger.debug(f"Available products for matching: {len(available_products)}")
        
        outfits = []
        product_map = {p.product_id: p for p in available_products}
        
        outfit_sections = llm_response.split("Outfit")
        logger.debug(f"Found {len(outfit_sections)-1} outfit sections in LLM response")
        
        for i, section in enumerate(outfit_sections[1:], 1):
            try:
                logger.debug(f"Processing outfit section {i}")
                outfit_items = []
                total_price = 0
                
                # Track which products are matched
                matched_products = []
                
                for product in available_products:
                    if product.product_id in section or product.name in section:
                        outfit_item = OutfitItem(
                            product=product,
                            styling_notes=f"Part of Outfit {i}",
                            role_in_outfit=self._determine_role(product.category.value)
                        )
                        outfit_items.append(outfit_item)
                        matched_products.append(product.product_id)
                        total_price += product.get_display_price()
                
                logger.debug(f"Outfit {i}: matched {len(matched_products)} products: {matched_products}")
                
                if outfit_items:
                    styling_tips = self._extract_styling_tips(section)
                    outfit = OutfitRecommendation(
                        outfit_id=str(uuid.uuid4()),
                        name=f"Outfit {i}",
                        description=section[:200] if section else f"Stylish outfit combination {i}",
                        items=outfit_items,
                        total_price=total_price,
                        styling_tips=styling_tips,
                        confidence_score=0.85
                    )
                    outfits.append(outfit)
                    logger.debug(f"Created outfit {i}: '{outfit.name}' with {len(outfit_items)} items, ${total_price:.2f}")
                else:
                    logger.debug(f"No products matched for outfit section {i}")
                    
            except Exception as e:
                logger.error(f"Error parsing outfit {i}: {e}", exc_info=True)
                continue
        
        if not outfits and available_products:
            logger.info(f"No outfits parsed from LLM response, creating default outfit")
            default_outfit = await self._create_default_outfit(available_products[:3])
            if default_outfit:
                outfits.append(default_outfit)
                logger.debug(f"Created default outfit with {len(default_outfit.items)} items")
        
        logger.debug(f"Final outfit parsing result: {len(outfits)} outfits created")
        return outfits
    
    async def _create_outfit_from_products(
        self,
        products: List[Product],
        user_profile: Optional[UserProfile] = None
    ) -> Optional[OutfitRecommendation]:
        if not products:
            return None
        
        outfit_items = []
        total_price = 0
        
        for product in products:
            outfit_item = OutfitItem(
                product=product,
                role_in_outfit=self._determine_role(product.category.value)
            )
            outfit_items.append(outfit_item)
            total_price += product.get_display_price()
        
        return OutfitRecommendation(
            outfit_id=str(uuid.uuid4()),
            name="Curated Outfit",
            description="A carefully selected outfit combination",
            items=outfit_items,
            total_price=total_price,
            styling_tips=["Mix and match these pieces for a cohesive look"],
            confidence_score=0.75
        )
    
    async def _create_default_outfit(self, products: List[Product]) -> Optional[OutfitRecommendation]:
        if not products:
            return None
        
        outfit_items = []
        total_price = 0
        
        for product in products:
            outfit_item = OutfitItem(
                product=product,
                styling_notes="Versatile piece for various occasions",
                role_in_outfit=self._determine_role(product.category.value)
            )
            outfit_items.append(outfit_item)
            total_price += product.get_display_price()
        
        return OutfitRecommendation(
            outfit_id=str(uuid.uuid4()),
            name="Recommended Style",
            description="A versatile outfit combination based on your preferences",
            items=outfit_items,
            total_price=total_price,
            styling_tips=[
                "These pieces work well together",
                "Can be dressed up or down depending on accessories",
                "Perfect for multiple occasions"
            ],
            confidence_score=0.7
        )
    
    def _determine_role(self, category: str) -> str:
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
    
    def _extract_styling_tips(self, text: str) -> List[str]:
        logger.debug(f"Extracting styling tips from text ({len(text)} characters)")
        tips = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['tip', 'style', 'wear', 'pair', 'add']):
                if len(line) > 10 and len(line) < 200:
                    tips.append(line.strip('- •'))
        
        result_tips = tips[:3] if tips else ["Style with confidence"]
        logger.debug(f"Extracted {len(result_tips)} styling tips")
        return result_tips
    
    def _generate_personalization_notes(self, profile: Optional[UserProfile]) -> Optional[str]:
        if not profile:
            return None
        
        notes = []
        
        if profile.body_type:
            notes.append(f"Recommendations tailored for {profile.body_type.value} body type")
        
        if profile.style_preferences and profile.style_preferences.style_personalities:
            styles = ", ".join([s.value for s in profile.style_preferences.style_personalities])
            notes.append(f"Focused on {styles} style preferences")
        
        if profile.budget_max:
            notes.append(f"Within budget of ${profile.budget_max:.2f}")
        
        return ". ".join(notes) if notes else None
    
    async def _get_product_by_id(self, product_id: str) -> Optional[Product]:
        from models import Category, ProductAttribute
        
        return Product(
            product_id=product_id,
            name=f"Product {product_id}",
            category=Category.TOPS,
            description="Fashion item",
            attributes=ProductAttribute(),
            price=99.99
        )
    
    def _create_empty_response(self, query: str, message: str) -> StylistResponse:
        return StylistResponse(
            response_id=str(uuid.uuid4()),
            user_query=query,
            recommendations=[],
            styling_advice=message
        )
    
    def _create_error_response(self, query: str, error: str) -> StylistResponse:
        return StylistResponse(
            response_id=str(uuid.uuid4()),
            user_query=query,
            recommendations=[],
            styling_advice=f"I encountered an issue while processing your request. Please try again or rephrase your query."
        )