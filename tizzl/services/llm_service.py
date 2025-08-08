import openai
import anthropic
from typing import List, Dict, Any, Optional
import json
import logging
from core.config import settings
from core.prompts import PromptTemplates

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.provider = "openai"
        
        if settings.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            self.provider = "openai"
        elif settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.provider = "anthropic"
        else:
            logger.warning("No LLM API key configured. Using mock responses.")
            self.provider = "mock"
    
    async def generate_outfit_recommendations(
        self,
        query: str,
        products: List[Any],
        user_profile: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        try:
            system_prompt = PromptTemplates.get_stylist_system_prompt()
            user_prompt = PromptTemplates.build_outfit_recommendation_prompt(
                query, products, user_profile, context
            )
            
            return await self._generate_response(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error generating outfit recommendations: {e}")
            return self._get_fallback_recommendations()
    
    async def generate_style_advice(
        self,
        query: str,
        user_profile: Optional[Any] = None
    ) -> str:
        try:
            system_prompt = PromptTemplates.get_stylist_system_prompt()
            user_prompt = PromptTemplates.build_style_advice_prompt(query, user_profile)
            
            return await self._generate_response(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error generating style advice: {e}")
            return "I'd be happy to help with your style question. Could you please provide more details?"
    
    async def enhance_search_query(self, query: str) -> List[str]:
        try:
            prompt = PromptTemplates.build_product_search_enhancement_prompt(query)
            response = await self._generate_response(
                "You are a fashion search expert. Extract relevant search terms.",
                prompt
            )
            
            terms = []
            for line in response.split('\n'):
                line = line.strip().strip('-').strip('•').strip()
                if line and len(line) > 2:
                    terms.append(line)
            
            return terms[:10]
        except Exception as e:
            logger.error(f"Error enhancing search query: {e}")
            return [query]
    
    async def rerank_products(
        self,
        query: str,
        products: List[Any]
    ) -> List[str]:
        try:
            prompt = PromptTemplates.build_reranking_prompt(query, products)
            response = await self._generate_response(
                "You are a fashion expert who ranks products by relevance.",
                prompt
            )
            
            product_ids = []
            for line in response.split('\n'):
                if 'Product ID:' in line or any(p.product_id in line for p in products):
                    for p in products:
                        if p.product_id in line:
                            if p.product_id not in product_ids:
                                product_ids.append(p.product_id)
            
            remaining_ids = [p.product_id for p in products if p.product_id not in product_ids]
            product_ids.extend(remaining_ids)
            
            return product_ids
        except Exception as e:
            logger.error(f"Error reranking products: {e}")
            return [p.product_id for p in products]
    
    async def _generate_response(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "openai" and self.openai_client:
            return await self._generate_openai_response(system_prompt, user_prompt)
        elif self.provider == "anthropic" and self.anthropic_client:
            return await self._generate_anthropic_response(system_prompt, user_prompt)
        else:
            return self._generate_mock_response(user_prompt)
    
    async def _generate_openai_response(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_anthropic_response(self, system_prompt: str, user_prompt: str) -> str:
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _generate_mock_response(self, user_prompt: str) -> str:
        # Check for specific item requests (like "what top goes with...")
        if any(phrase in user_prompt.lower() for phrase in ["what top", "suggest a top", "top to go with", "what goes with", "pair with"]):
            return """For dark bootcut denim, here are some great top options:

**Classic Button-Down Shirt** (Product ID: SKU003)
- White or light blue works beautifully with dark denim
- Can be worn tucked in for polish or untucked for casual
- Roll up sleeves for a relaxed vibe

**Fitted Black Turtleneck** (Product ID: SKU004)  
- Creates a sleek, sophisticated silhouette
- Perfect for cooler weather
- Easily dressed up or down with accessories

**Soft Knit Sweater** (Product ID: SKU005)
- Choose cream, camel, or navy for versatility
- The relaxed fit balances the fitted bootcut silhouette
- Great for layering

**Styling Tips:**
- Bootcut jeans work best with fitted tops to balance proportions
- Tuck in blouses and shirts to define your waistline
- Add a belt to enhance the silhouette"""
        elif "outfit" in user_prompt.lower():
            return """
**Outfit 1: Casual Weekend Brunch**
- Classic White Cotton T-Shirt (Product ID: SKU001)
- High-Waisted Black Denim Jeans (Product ID: SKU002)
- Canvas Low-Top Sneakers (Product ID: SKU005)
- Leather Crossbody Bag (Product ID: SKU008)

This combination creates the perfect casual yet put-together look for weekend brunch. The classic white tee and black jeans combo is timeless, while the sneakers keep it comfortable.

**Styling Tips:**
- Tuck in the t-shirt for a more polished look
- Roll up the jeans slightly to show off the sneakers
- The crossbody bag keeps hands free for coffee and conversation

**Outfit 2: Elevated Casual**
- Silk Midi Wrap Dress (Product ID: SKU003)
- Canvas Low-Top Sneakers (Product ID: SKU005)

For a more feminine approach, the silk dress dressed down with sneakers creates an effortlessly chic brunch outfit.

**Styling Tips:**
- Choose the navy colorway for versatility
- Add delicate jewelry for subtle elegance
- Perfect for outdoor brunch settings
"""
        else:
            return "Here's some general style advice based on your query. For more specific recommendations, please provide additional details about your preferences and needs."
    
    def _get_fallback_recommendations(self) -> str:
        return """I've found some great pieces that could work for you! 
        
While I'm having trouble accessing specific recommendations right now, I suggest:
1. Starting with versatile basics that match your style
2. Building outfits around a statement piece
3. Considering the occasion and comfort level

Please try refining your search or let me know more about what you're looking for!"""