from typing import List, Optional, Dict, Any
import uuid
import time
import logging
from ..models import (
    Product, UserProfile, UserQuery, 
    StylistResponse, OutfitRecommendation, OutfitItem
)
from .retrieval_service import RetrievalService
from .llm_service import LLMService
from ..core.config import settings

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
        
        try:
            products = await self.retrieval_service.retrieve_products(query, user_profile)
            
            if not products:
                return self._create_empty_response(query.query, "No matching products found")
            
            llm_response = await self.llm_service.generate_outfit_recommendations(
                query.query,
                products,
                user_profile,
                query.context
            )
            
            outfits = await self._parse_outfit_recommendations(llm_response, products)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return StylistResponse(
                response_id=str(uuid.uuid4()),
                user_query=query.query,
                recommendations=outfits,
                individual_items=products[:5],
                styling_advice=llm_response,
                personalization_notes=self._generate_personalization_notes(user_profile),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error getting styling recommendations: {e}")
            return self._create_error_response(query.query, str(e))
    
    async def get_outfit_for_product(
        self,
        product_id: str,
        user_profile: Optional[UserProfile] = None
    ) -> List[OutfitRecommendation]:
        try:
            product = await self._get_product_by_id(product_id)
            if not product:
                return []
            
            outfit_combinations = await self.retrieval_service.get_outfit_combinations(product)
            
            outfits = []
            for combo in outfit_combinations:
                outfit = await self._create_outfit_from_products(combo, user_profile)
                if outfit:
                    outfits.append(outfit)
            
            return outfits
            
        except Exception as e:
            logger.error(f"Error getting outfit for product: {e}")
            return []
    
    async def get_similar_styles(
        self,
        product_id: str,
        top_k: int = 10
    ) -> List[Product]:
        try:
            return await self.retrieval_service.find_similar_items(product_id, top_k)
        except Exception as e:
            logger.error(f"Error getting similar styles: {e}")
            return []
    
    async def get_style_advice(
        self,
        query: str,
        user_profile: Optional[UserProfile] = None
    ) -> str:
        try:
            return await self.llm_service.generate_style_advice(query, user_profile)
        except Exception as e:
            logger.error(f"Error getting style advice: {e}")
            return "I'd be happy to help with your style question. Please try rephrasing or provide more details."
    
    async def _parse_outfit_recommendations(
        self,
        llm_response: str,
        available_products: List[Product]
    ) -> List[OutfitRecommendation]:
        outfits = []
        product_map = {p.product_id: p for p in available_products}
        
        outfit_sections = llm_response.split("Outfit")
        
        for i, section in enumerate(outfit_sections[1:], 1):
            try:
                outfit_items = []
                total_price = 0
                
                for product in available_products:
                    if product.product_id in section or product.name in section:
                        outfit_item = OutfitItem(
                            product=product,
                            styling_notes=f"Part of Outfit {i}",
                            role_in_outfit=self._determine_role(product.category.value)
                        )
                        outfit_items.append(outfit_item)
                        total_price += product.get_display_price()
                
                if outfit_items:
                    outfit = OutfitRecommendation(
                        outfit_id=str(uuid.uuid4()),
                        name=f"Outfit {i}",
                        description=section[:200] if section else f"Stylish outfit combination {i}",
                        items=outfit_items,
                        total_price=total_price,
                        styling_tips=self._extract_styling_tips(section),
                        confidence_score=0.85
                    )
                    outfits.append(outfit)
                    
            except Exception as e:
                logger.error(f"Error parsing outfit {i}: {e}")
                continue
        
        if not outfits and available_products:
            default_outfit = await self._create_default_outfit(available_products[:3])
            if default_outfit:
                outfits.append(default_outfit)
        
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
        tips = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['tip', 'style', 'wear', 'pair', 'add']):
                if len(line) > 10 and len(line) < 200:
                    tips.append(line.strip('- •'))
        
        return tips[:3] if tips else ["Style with confidence"]
    
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
        from ..models import Category, ProductAttribute
        
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