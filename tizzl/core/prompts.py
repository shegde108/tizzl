from typing import List, Dict, Any, Optional
from tizzl.models import Product, UserProfile, UserQuery

class PromptTemplates:
    
    @staticmethod
    def get_stylist_system_prompt() -> str:
        return """You are an expert fashion stylist with years of experience in personal styling, 
fashion trends, and outfit coordination. You have deep knowledge of:
- Color theory and coordination
- Body types and flattering silhouettes  
- Occasion-appropriate dressing
- Current and classic fashion trends
- Mixing high and low-end pieces
- Accessorizing and layering techniques
- Seasonal styling

Your goal is to provide personalized, practical, and inspiring fashion advice that helps 
users look and feel their best. Be encouraging, specific, and consider the user's 
individual style preferences, body type, and lifestyle needs."""
    
    @staticmethod
    def build_outfit_recommendation_prompt(
        query: str,
        products: List[Product],
        user_profile: Optional[UserProfile] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        products_text = PromptTemplates._format_products(products)
        user_context = PromptTemplates._format_user_context(user_profile) if user_profile else ""
        
        prompt = f"""Based on the following request and available inventory, create personalized outfit recommendations:

USER REQUEST: {query}

{user_context}

AVAILABLE PRODUCTS:
{products_text}

Please provide:
1. 2-3 complete outfit recommendations using the available products
2. Explain why each piece works well together
3. Styling tips for each outfit
4. Alternative options if certain items aren't perfect
5. Accessories or additional pieces that would complete the look

Format your response as:
- Clear outfit groupings
- Specific product references by name and ID
- Practical styling advice
- Consider the user's body type, preferences, and occasion if mentioned

Be specific about colors, patterns, and how pieces complement each other."""
        
        return prompt
    
    @staticmethod
    def build_style_advice_prompt(
        query: str,
        user_profile: Optional[UserProfile] = None
    ) -> str:
        user_context = PromptTemplates._format_user_context(user_profile) if user_profile else ""
        
        return f"""Provide expert fashion advice for the following question:

QUESTION: {query}

{user_context}

Please provide:
1. Direct answer to the question
2. Practical tips and recommendations
3. Common mistakes to avoid
4. Specific examples when helpful
5. Additional considerations based on body type, lifestyle, or preferences

Keep advice actionable and encouraging."""
    
    @staticmethod
    def build_product_search_enhancement_prompt(query: str) -> str:
        return f"""Extract and enhance search keywords from this fashion query:

QUERY: {query}

Identify:
1. Specific product types mentioned
2. Colors, patterns, or materials
3. Occasions or use cases
4. Style preferences (casual, formal, trendy, classic, etc.)
5. Any implicit requirements (weather, season, formality level)

Return a list of search terms that would help find relevant products.
Include synonyms and related terms."""
    
    @staticmethod
    def build_outfit_compatibility_prompt(items: List[Product]) -> str:
        items_text = PromptTemplates._format_products(items)
        
        return f"""Evaluate if these items work well together as an outfit:

ITEMS:
{items_text}

Analyze:
1. Color compatibility (do the colors work together?)
2. Style cohesion (do the styles match?)
3. Formality level consistency
4. Pattern mixing (if applicable)
5. Proportions and silhouette balance

Provide:
- Compatibility score (1-10)
- What works well
- Potential issues
- Suggestions for improvement"""
    
    @staticmethod
    def _format_products(products: List[Product]) -> str:
        formatted = []
        for p in products:
            colors = ", ".join(p.attributes.color) if p.attributes.color else "N/A"
            occasions = ", ".join([o.value for o in p.attributes.occasion]) if p.attributes.occasion else "N/A"
            
            formatted.append(f"""
Product ID: {p.product_id}
Name: {p.name}
Category: {p.category.value}
Price: ${p.get_display_price():.2f}
Colors: {colors}
Description: {p.description[:200]}...
Style: {p.attributes.style or 'N/A'}
Occasions: {occasions}
Material: {p.attributes.material or 'N/A'}
""")
        return "\n".join(formatted)
    
    @staticmethod
    def _format_user_context(profile: UserProfile) -> str:
        if not profile:
            return ""
        
        parts = ["USER PROFILE:"]
        
        if profile.body_type:
            parts.append(f"Body Type: {profile.body_type.value}")
        
        if profile.style_preferences:
            prefs = profile.style_preferences
            if prefs.style_personalities:
                parts.append(f"Style: {', '.join([s.value for s in prefs.style_personalities])}")
            if prefs.preferred_colors:
                parts.append(f"Preferred Colors: {', '.join(prefs.preferred_colors)}")
            if prefs.avoided_colors:
                parts.append(f"Avoided Colors: {', '.join(prefs.avoided_colors)}")
        
        if profile.budget_max:
            parts.append(f"Budget: Up to ${profile.budget_max:.2f}")
        
        if profile.sizes:
            sizes_text = ", ".join([f"{k}: {v}" for k, v in profile.sizes.items()])
            parts.append(f"Sizes: {sizes_text}")
        
        return "\n".join(parts)
    
    @staticmethod
    def build_reranking_prompt(query: str, products: List[Product]) -> str:
        products_text = PromptTemplates._format_products(products)
        
        return f"""Rank these products by relevance to the user's query:

QUERY: {query}

PRODUCTS:
{products_text}

Consider:
1. Direct relevance to the query
2. Style appropriateness
3. Versatility and outfit potential
4. Value for money
5. Trending or classic appeal

Return a ranked list of product IDs from most to least relevant, with brief reasoning."""