from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class BodyType(str, Enum):
    PEAR = "pear"
    APPLE = "apple"
    HOURGLASS = "hourglass"
    RECTANGLE = "rectangle"
    INVERTED_TRIANGLE = "inverted_triangle"
    ATHLETIC = "athletic"

class StylePersonality(str, Enum):
    CLASSIC = "classic"
    TRENDY = "trendy"
    BOHEMIAN = "bohemian"
    MINIMALIST = "minimalist"
    EDGY = "edgy"
    ROMANTIC = "romantic"
    SPORTY = "sporty"
    GLAMOROUS = "glamorous"

class StylePreference(BaseModel):
    preferred_colors: List[str] = Field(default_factory=list)
    avoided_colors: List[str] = Field(default_factory=list)
    preferred_patterns: List[str] = Field(default_factory=list)
    avoided_patterns: List[str] = Field(default_factory=list)
    preferred_brands: List[str] = Field(default_factory=list)
    style_personalities: List[StylePersonality] = Field(default_factory=list)
    preferred_fit: Optional[str] = None
    sustainability_preference: bool = False
    comfort_priority: int = Field(default=5, ge=1, le=10)

class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    body_type: Optional[BodyType] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    sizes: Dict[str, str] = Field(default_factory=dict)
    style_preferences: StylePreference = Field(default_factory=StylePreference)
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    location: Optional[str] = None
    purchase_history: List[str] = Field(default_factory=list)
    wishlist: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserQuery(BaseModel):
    query: str
    user_id: Optional[str] = None
    occasion: Optional[str] = None
    budget: Optional[float] = None
    preferred_categories: List[str] = Field(default_factory=list)
    excluded_categories: List[str] = Field(default_factory=list)
    color_preferences: List[str] = Field(default_factory=list)
    size_filters: Dict[str, str] = Field(default_factory=dict)
    include_sale_items: bool = True
    max_results: int = 20
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None