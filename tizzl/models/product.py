from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class Category(str, Enum):
    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"
    SHOES = "shoes"
    ACCESSORIES = "accessories"
    BAGS = "bags"
    JEWELRY = "jewelry"

class Occasion(str, Enum):
    CASUAL = "casual"
    WORK = "work"
    FORMAL = "formal"
    COCKTAIL = "cocktail"
    ATHLETIC = "athletic"
    BEACH = "beach"
    PARTY = "party"

class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL_SEASON = "all_season"

class ProductAttribute(BaseModel):
    color: List[str] = Field(default_factory=list)
    pattern: Optional[str] = None
    material: Optional[str] = None
    occasion: List[Occasion] = Field(default_factory=list)
    season: List[Season] = Field(default_factory=list)
    style: Optional[str] = None
    brand: Optional[str] = None
    fit: Optional[str] = None
    care_instructions: Optional[str] = None

class ProductEmbedding(BaseModel):
    text_embedding: Optional[List[float]] = None
    visual_embedding: Optional[List[float]] = None
    combined_embedding: Optional[List[float]] = None
    embedding_model: str = "text-embedding-3-small"
    created_at: datetime = Field(default_factory=datetime.now)

class Product(BaseModel):
    product_id: str
    name: str
    category: Category
    subcategory: Optional[str] = None
    description: str
    attributes: ProductAttribute
    price: float
    sale_price: Optional[float] = None
    currency: str = "USD"
    sizes: List[str] = Field(default_factory=list)
    in_stock: bool = True
    images: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    embeddings: Optional[ProductEmbedding] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def get_display_price(self) -> float:
        return self.sale_price if self.sale_price else self.price
    
    def to_search_text(self) -> str:
        parts = [
            self.name,
            self.description,
            f"Category: {self.category.value}",
            f"Subcategory: {self.subcategory}" if self.subcategory else "",
            f"Colors: {', '.join(self.attributes.color)}" if self.attributes.color else "",
            f"Pattern: {self.attributes.pattern}" if self.attributes.pattern else "",
            f"Material: {self.attributes.material}" if self.attributes.material else "",
            f"Style: {self.attributes.style}" if self.attributes.style else "",
            f"Brand: {self.attributes.brand}" if self.attributes.brand else "",
            f"Occasions: {', '.join([o.value for o in self.attributes.occasion])}" if self.attributes.occasion else "",
            f"Seasons: {', '.join([s.value for s in self.attributes.season])}" if self.attributes.season else "",
        ]
        return " ".join(filter(None, parts))