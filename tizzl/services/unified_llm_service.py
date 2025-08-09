import openai
import anthropic
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
import asyncio
from core.config import settings
from models import Product, UserProfile

logger = logging.getLogger(__name__)

class UnifiedLLMService:
    """
    Unified LLM service that combines all LLM operations into a single call
    to reduce latency and API costs
    """
    
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
    
    async def process_styling_query(
        self,
        query: str,
        products: List[Product],
        user_profile: Optional[UserProfile] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a styling query in a single LLM call that:
        1. Enhances search terms
        2. Ranks products by relevance
        3. Generates outfit recommendations
        
        Returns a structured response with all components
        """
        try:
            system_prompt = self._build_unified_system_prompt()
            user_prompt = self._build_unified_user_prompt(query, products, user_profile, context)
            
            # Make single LLM call with structured output
            response = await self._generate_structured_response(system_prompt, user_prompt)
            
            # Parse and validate response
            result = self._parse_unified_response(response, products)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in unified LLM processing: {e}")
            return self._get_fallback_unified_response(query, products)
    
    def _build_unified_system_prompt(self) -> str:
        """Build the unified system prompt for all operations"""
        return """You are an expert AI fashion stylist that processes styling queries efficiently.

Your response must be valid JSON with this exact structure:
{
    "search_terms": ["term1", "term2", ...],
    "product_rankings": [
        {"product_id": "id", "score": 0.95, "reason": "brief reason"},
        ...
    ],
    "outfits": [
        {
            "name": "Outfit Name",
            "description": "Brief description",
            "product_ids": ["id1", "id2", ...],
            "styling_tips": ["tip1", "tip2"],
            "total_price": 299.99
        },
        ...
    ],
    "styling_advice": "Overall styling advice and recommendations"
}

Guidelines:
1. Extract 3-5 relevant search terms from the query
2. Rank ALL provided products by relevance (0-1 score)
3. ALWAYS create 2-3 complete outfits using the most relevant products, even for general advice queries
4. Keep styling_advice brief (1-2 sentences) and focus on product recommendations
5. Ensure all product_ids reference actual products from the input
6. Prioritize showing products over giving advice - users want to see items from inventory"""
    
    def _build_unified_user_prompt(
        self,
        query: str,
        products: List[Product],
        user_profile: Optional[UserProfile],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the unified user prompt with all necessary information"""
        
        # Format products concisely
        products_text = self._format_products_concise(products)
        
        # Format user context if available
        user_context = ""
        if user_profile:
            user_context = f"\nUser Preferences: "
            if user_profile.style_preferences:
                prefs = user_profile.style_preferences
                if prefs.style_personalities:
                    user_context += f"Style: {', '.join([s.value for s in prefs.style_personalities])}. "
                if prefs.preferred_colors:
                    user_context += f"Colors: {', '.join(prefs.preferred_colors)}. "
            if user_profile.budget_max:
                user_context += f"Budget: ${user_profile.budget_max:.0f}"
        
        prompt = f"""Process this request and return structured JSON with product recommendations:

QUERY: {query}{user_context}

AVAILABLE PRODUCTS (ID, Name, Category, Price):
{products_text}

Remember to:
1. Extract search terms
2. Rank ALL products with scores
3. ALWAYS create 2-3 outfits from available products
4. Keep styling advice brief (focus on showing products)
5. Return valid JSON only

Even for general advice queries, prioritize showing actual products from inventory."""
        
        return prompt
    
    def _format_products_concise(self, products: List[Product]) -> str:
        """Format products in a concise way to reduce tokens"""
        lines = []
        for p in products[:30]:  # Limit to top 30 products
            colors = ','.join(p.attributes.color[:2]) if p.attributes.color else 'N/A'
            lines.append(
                f"{p.product_id}|{p.name[:30]}|{p.category.value}|${p.get_display_price():.0f}|{colors}"
            )
        return '\n'.join(lines)
    
    async def _generate_structured_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response from LLM with structured output"""
        if self.provider == "openai" and self.openai_client:
            return await self._generate_openai_structured(system_prompt, user_prompt)
        elif self.provider == "anthropic" and self.anthropic_client:
            return await self._generate_anthropic_structured(system_prompt, user_prompt)
        else:
            return self._generate_mock_structured()
    
    async def _generate_openai_structured(self, system_prompt: str, user_prompt: str) -> str:
        """Generate structured response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500,  # Reduced from 2000
                response_format={"type": "json_object"}  # Force JSON output
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI structured generation error: {e}")
            raise
    
    async def _generate_anthropic_structured(self, system_prompt: str, user_prompt: str) -> str:
        """Generate structured response using Anthropic"""
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.7,
                system=system_prompt + "\n\nAlways respond with valid JSON.",
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic structured generation error: {e}")
            raise
    
    def _generate_mock_structured(self) -> str:
        """Generate mock structured response for testing"""
        return json.dumps({
            "search_terms": ["casual", "summer", "comfortable", "versatile", "everyday"],
            "product_rankings": [
                {"product_id": "SKU001", "score": 0.95, "reason": "Perfect for request"},
                {"product_id": "SKU002", "score": 0.90, "reason": "Great match"},
                {"product_id": "SKU003", "score": 0.85, "reason": "Good option"},
                {"product_id": "SKU004", "score": 0.75, "reason": "Alternative choice"},
                {"product_id": "SKU005", "score": 0.70, "reason": "Can work"}
            ],
            "outfits": [
                {
                    "name": "Casual Chic",
                    "description": "Perfect everyday outfit",
                    "product_ids": ["SKU001", "SKU002", "SKU005"],
                    "styling_tips": ["Tuck in the top", "Add a belt for definition"],
                    "total_price": 189.99
                },
                {
                    "name": "Weekend Ready",
                    "description": "Comfortable and stylish",
                    "product_ids": ["SKU003", "SKU004"],
                    "styling_tips": ["Roll up sleeves", "Pair with sneakers"],
                    "total_price": 149.99
                }
            ],
            "styling_advice": "These versatile pieces can be mixed and matched for various occasions. Focus on comfortable fabrics and classic silhouettes that transition easily from day to night."
        })
    
    def _parse_unified_response(self, response: str, products: List[Product]) -> Dict[str, Any]:
        """Parse and validate the unified LLM response"""
        try:
            # Parse JSON response
            data = json.loads(response)
            
            # Create product map for quick lookup
            product_map = {p.product_id: p for p in products}
            
            # Validate and enhance the response
            result = {
                'search_terms': data.get('search_terms', []),
                'ranked_products': [],
                'outfits': [],
                'styling_advice': data.get('styling_advice', '')
            }
            
            # Process product rankings
            for ranking in data.get('product_rankings', []):
                pid = ranking.get('product_id')
                if pid in product_map:
                    result['ranked_products'].append({
                        'product': product_map[pid],
                        'score': ranking.get('score', 0.5),
                        'reason': ranking.get('reason', '')
                    })
            
            # Process outfits
            for outfit_data in data.get('outfits', []):
                outfit_products = []
                total_price = 0
                
                for pid in outfit_data.get('product_ids', []):
                    if pid in product_map:
                        outfit_products.append(product_map[pid])
                        total_price += product_map[pid].get_display_price()
                
                if outfit_products:
                    result['outfits'].append({
                        'name': outfit_data.get('name', 'Outfit'),
                        'description': outfit_data.get('description', ''),
                        'products': outfit_products,
                        'styling_tips': outfit_data.get('styling_tips', []),
                        'total_price': total_price
                    })
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return self._get_fallback_unified_response("", products)
        except Exception as e:
            logger.error(f"Error parsing unified response: {e}")
            return self._get_fallback_unified_response("", products)
    
    def _get_fallback_unified_response(self, query: str, products: List[Product]) -> Dict[str, Any]:
        """Fallback response when LLM fails"""
        # Use first 5 products as fallback
        selected_products = products[:5] if products else []
        
        return {
            'search_terms': [query] if query else ['fashion', 'style'],
            'ranked_products': [
                {'product': p, 'score': 0.7, 'reason': 'Recommended item'}
                for p in selected_products
            ],
            'outfits': [
                {
                    'name': 'Suggested Look',
                    'description': 'A versatile outfit combination',
                    'products': selected_products[:3],
                    'styling_tips': ['Mix and match as desired'],
                    'total_price': sum(p.get_display_price() for p in selected_products[:3])
                }
            ] if selected_products else [],
            'styling_advice': 'Here are some great options for you. Feel free to mix and match!'
        }
    
    async def generate_simple_advice(self, query: str) -> str:
        """Generate simple style advice without product context"""
        try:
            system_prompt = "You are a helpful fashion advisor. Provide brief, actionable style advice."
            user_prompt = f"Provide style advice for: {query}\n\nKeep response under 150 words."
            
            if self.provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                return response.choices[0].message.content
            elif self.provider == "anthropic" and self.anthropic_client:
                message = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=200,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return message.content[0].text
            else:
                return "I'd be happy to help with your style question. Could you provide more details about what you're looking for?"
                
        except Exception as e:
            logger.error(f"Error generating simple advice: {e}")
            return "I'd be happy to help with style advice. Please try rephrasing your question."