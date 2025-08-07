from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import hashlib
import json

from services.retailer_integration import RetailerRecommendationService
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/retailer", tags=["retailer"])

# Initialize service (can be configured with actual retailer API)
retailer_service = RetailerRecommendationService(
    retailer_api_url=getattr(settings, 'retailer_api_url', None),
    api_key=getattr(settings, 'retailer_api_key', None)
)

class ProductInteractionRequest(BaseModel):
    product_id: str = Field(..., description="ID of the product interacted with")
    user_id: Optional[str] = Field(None, description="User identifier")
    interaction_type: str = Field("click", description="Type of interaction: click, like, add_to_cart, view_details")
    session_id: Optional[str] = Field(None, description="Chat session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for recommendations")

class BatchInteractionRequest(BaseModel):
    interactions: List[ProductInteractionRequest] = Field(..., description="List of product interactions")
    create_outfit: bool = Field(False, description="Whether to create an outfit from interactions")

class InteractionHistoryResponse(BaseModel):
    session_id: Optional[str]
    user_id: Optional[str]
    interactions: List[Dict[str, Any]]
    total_count: int

@router.post("/recommendations")
async def get_product_recommendations(request: ProductInteractionRequest):
    """
    Get retailer recommendations based on product interaction in the stylist chat.
    
    This endpoint is called when a user clicks on or likes a product in the AI stylist interface.
    It fetches recommendations from the retailer's system and enhances them with styling context.
    """
    try:
        recommendations = await retailer_service.get_retailer_recommendations(
            product_id=request.product_id,
            user_id=request.user_id,
            interaction_type=request.interaction_type,
            session_id=request.session_id,
            context=request.context
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting retailer recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/batch")
async def get_batch_recommendations(request: BatchInteractionRequest):
    """
    Process multiple product interactions and get aggregated recommendations.
    
    Useful when users interact with multiple products in quick succession.
    """
    try:
        all_recommendations = []
        product_ids = []
        
        for interaction in request.interactions:
            product_ids.append(interaction.product_id)
            
            recs = await retailer_service.get_retailer_recommendations(
                product_id=interaction.product_id,
                user_id=interaction.user_id,
                interaction_type=interaction.interaction_type,
                session_id=interaction.session_id,
                context=interaction.context
            )
            
            if recs.get("status") == "success":
                all_recommendations.extend(recs.get("recommendations", []))
        
        # Remove duplicates and sort by score
        unique_recs = {}
        for rec in all_recommendations:
            pid = rec.get("product_id")
            if pid not in unique_recs or rec.get("score", 0) > unique_recs[pid].get("score", 0):
                unique_recs[pid] = rec
        
        sorted_recs = sorted(unique_recs.values(), key=lambda x: x.get("score", 0), reverse=True)
        
        response = {
            "status": "success",
            "recommendations": sorted_recs[:20],  # Top 20 recommendations
            "interaction_count": len(request.interactions)
        }
        
        # Optionally create an outfit from the interactions
        if request.create_outfit and product_ids:
            outfit = await retailer_service.create_outfit_from_interactions(
                product_ids, 
                request.interactions[0].user_id if request.interactions else None
            )
            response["suggested_outfit"] = outfit
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing batch recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactions/history")
async def get_interaction_history(
    session_id: Optional[str] = Query(None, description="Session ID to filter by"),
    user_id: Optional[str] = Query(None, description="User ID to filter by")
):
    """
    Get the history of product interactions for a session or user.
    
    Useful for understanding user preferences and behavior patterns.
    """
    try:
        if not session_id and not user_id:
            raise HTTPException(
                status_code=400,
                detail="Either session_id or user_id must be provided"
            )
        
        history = await retailer_service.get_interaction_history(
            session_id=session_id or "",
            user_id=user_id
        )
        
        return InteractionHistoryResponse(
            session_id=session_id,
            user_id=user_id,
            interactions=history,
            total_count=len(history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interaction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outfit/from-interactions")
async def create_outfit_from_interactions(
    product_ids: List[str] = Body(..., description="List of product IDs to create outfit from"),
    user_id: Optional[str] = Body(None, description="User identifier")
):
    """
    Create an outfit recommendation based on products the user has interacted with.
    
    This combines multiple liked/clicked products into a cohesive outfit.
    """
    try:
        if not product_ids:
            raise HTTPException(
                status_code=400,
                detail="At least one product_id must be provided"
            )
        
        outfit = await retailer_service.create_outfit_from_interactions(
            product_ids=product_ids,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "outfit": outfit,
            "message": f"Created outfit with {len(product_ids)} items"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outfit from interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_recommendation_feedback(
    product_id: str = Body(..., description="Recommended product ID"),
    feedback_type: str = Body(..., description="Feedback type: helpful, not_helpful, purchased"),
    user_id: Optional[str] = Body(None, description="User identifier"),
    session_id: Optional[str] = Body(None, description="Session identifier"),
    notes: Optional[str] = Body(None, description="Additional feedback notes")
):
    """
    Submit feedback on retailer recommendations to improve future suggestions.
    """
    try:
        # In a real implementation, this would be sent to the retailer's analytics system
        feedback_data = {
            "product_id": product_id,
            "feedback_type": feedback_type,
            "user_id": user_id,
            "session_id": session_id,
            "notes": notes
        }
        
        logger.info(f"Recommendation feedback received: {feedback_data}")
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "feedback_id": hashlib.md5(
                json.dumps(feedback_data, sort_keys=True).encode()
            ).hexdigest()[:8]
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

