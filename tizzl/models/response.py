from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .product import Product

class OutfitItem(BaseModel):
    product: Product
    styling_notes: Optional[str] = None
    role_in_outfit: str

class OutfitRecommendation(BaseModel):
    outfit_id: str
    name: str
    description: str
    items: List[OutfitItem]
    total_price: float
    occasion: Optional[str] = None
    season: Optional[str] = None
    styling_tips: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    reasoning: Optional[str] = None

class StylistResponse(BaseModel):
    response_id: str
    user_query: str
    recommendations: List[OutfitRecommendation]
    individual_items: List[Product] = Field(default_factory=list)
    styling_advice: str
    personalization_notes: Optional[str] = None
    alternative_options: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = None