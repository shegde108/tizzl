from typing import List, Dict, Any, Optional
import httpx
import logging
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)

class RetailerRecommendationService:
    """
    Service to integrate with retailer's existing recommendation system.
    Handles interactions when users click/like products in the stylist chat.
    """
    
    def __init__(self, retailer_api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.retailer_api_url = retailer_api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.interaction_cache = {}
    
    async def get_retailer_recommendations(
        self,
        product_id: str,
        user_id: Optional[str] = None,
        interaction_type: str = "click",
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch recommendations from retailer's system based on product interaction.
        
        Args:
            product_id: ID of the product clicked/liked
            user_id: User identifier
            interaction_type: Type of interaction (click, like, add_to_cart, view_details)
            session_id: Current chat session ID
            context: Additional context (category preferences, price range, etc.)
        
        Returns:
            Dictionary containing retailer recommendations and metadata
        """
        try:
            # Record the interaction
            interaction_data = await self._record_interaction(
                product_id, user_id, interaction_type, session_id
            )
            
            # Get recommendations from retailer's API
            if self.retailer_api_url:
                recommendations = await self._fetch_external_recommendations(
                    product_id, user_id, context
                )
            else:
                # Fallback to mock recommendations for testing
                recommendations = await self._generate_mock_recommendations(
                    product_id, interaction_type, context
                )
            
            # Enhance recommendations with AI stylist context
            enhanced_recommendations = await self._enhance_with_stylist_context(
                recommendations, interaction_data, context
            )
            
            return {
                "status": "success",
                "interaction": interaction_data,
                "recommendations": enhanced_recommendations,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "retailer_api" if self.retailer_api_url else "mock",
                    "session_id": session_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting retailer recommendations: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": []
            }
    
    async def _record_interaction(
        self,
        product_id: str,
        user_id: Optional[str],
        interaction_type: str,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Record user interaction for analytics and personalization."""
        interaction = {
            "product_id": product_id,
            "user_id": user_id or "anonymous",
            "type": interaction_type,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id
        }
        
        # Cache interaction for session continuity
        cache_key = f"{session_id}:{product_id}"
        self.interaction_cache[cache_key] = interaction
        
        return interaction
    
    async def _fetch_external_recommendations(
        self,
        product_id: str,
        user_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fetch recommendations from retailer's external API."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            params = {
                "product_id": product_id,
                "limit": context.get("limit", 10) if context else 10
            }
            
            if user_id:
                params["user_id"] = user_id
            
            if context:
                if "categories" in context:
                    params["categories"] = ",".join(context["categories"])
                if "price_range" in context:
                    params["min_price"] = context["price_range"].get("min")
                    params["max_price"] = context["price_range"].get("max")
            
            response = await self.client.get(
                f"{self.retailer_api_url}/recommendations",
                headers=headers,
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("recommendations", [])
            
        except Exception as e:
            logger.error(f"Error fetching from retailer API: {e}")
            return []
    
    async def _generate_mock_recommendations(
        self,
        product_id: str,
        interaction_type: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate mock recommendations for testing."""
        # Create deterministic mock data based on product_id
        seed = int(hashlib.md5(product_id.encode()).hexdigest()[:8], 16)
        
        recommendation_types = {
            "click": ["similar_style", "same_category", "frequently_bought"],
            "like": ["similar_style", "complementary", "trending"],
            "add_to_cart": ["frequently_bought", "complementary", "bundle"],
            "view_details": ["similar_style", "same_brand", "price_similar"]
        }
        
        rec_type = recommendation_types.get(interaction_type, ["similar_style"])[0]
        
        recommendations = []
        for i in range(5):
            recommendations.append({
                "product_id": f"REC_{product_id}_{i}",
                "name": f"Recommended Item {i+1}",
                "reason": f"Based on your {interaction_type} of similar items",
                "type": rec_type,
                "score": 0.95 - (i * 0.1),
                "price": 50 + (seed % 100) + (i * 10),
                "category": context.get("categories", ["general"])[0] if context else "general"
            })
        
        return recommendations
    
    async def _enhance_with_stylist_context(
        self,
        recommendations: List[Dict[str, Any]],
        interaction_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance retailer recommendations with AI stylist context."""
        enhanced = []
        
        for rec in recommendations:
            enhanced_rec = rec.copy()
            
            # Add styling context based on interaction type
            if interaction_data["type"] == "like":
                enhanced_rec["styling_note"] = "This piece would pair beautifully with your liked item"
            elif interaction_data["type"] == "click":
                enhanced_rec["styling_note"] = "Customers who viewed this also loved this piece"
            elif interaction_data["type"] == "add_to_cart":
                enhanced_rec["styling_note"] = "Complete the look with this complementary piece"
            
            # Add outfit potential score
            enhanced_rec["outfit_potential"] = self._calculate_outfit_potential(
                rec, context
            )
            
            enhanced.append(enhanced_rec)
        
        # Sort by outfit potential and original score
        enhanced.sort(key=lambda x: (x.get("outfit_potential", 0), x.get("score", 0)), reverse=True)
        
        return enhanced
    
    def _calculate_outfit_potential(
        self,
        recommendation: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate how well this item fits into an outfit."""
        score = 0.5
        
        # Boost score based on recommendation type
        if recommendation.get("type") == "complementary":
            score += 0.3
        elif recommendation.get("type") == "frequently_bought":
            score += 0.2
        
        # Adjust based on context
        if context:
            if "occasion" in context and recommendation.get("occasion") == context["occasion"]:
                score += 0.1
            if "style_preference" in context and recommendation.get("style") == context["style_preference"]:
                score += 0.1
        
        return min(score, 1.0)
    
    async def get_interaction_history(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get interaction history for a session or user."""
        history = []
        
        for key, interaction in self.interaction_cache.items():
            if session_id in key or (user_id and interaction.get("user_id") == user_id):
                history.append(interaction)
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return history
    
    async def create_outfit_from_interactions(
        self,
        product_ids: List[str],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an outfit based on multiple product interactions."""
        outfit_items = []
        total_price = 0
        
        for product_id in product_ids:
            # Get product details (mock for now)
            product = {
                "product_id": product_id,
                "name": f"Product {product_id}",
                "price": 75.00
            }
            outfit_items.append(product)
            total_price += product["price"]
        
        return {
            "outfit_id": hashlib.md5(json.dumps(product_ids).encode()).hexdigest()[:8],
            "items": outfit_items,
            "total_price": total_price,
            "created_from": "user_interactions",
            "compatibility_score": 0.85
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()