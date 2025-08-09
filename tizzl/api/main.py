from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel

from models import Product, UserProfile, UserQuery, StylistResponse
from services.stylist_service import StylistService
from services.optimized_stylist_service import OptimizedStylistService
from core.vector_store import VectorStore
from core.config import settings
from utils.data_loader import DataLoader

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Stylist API",
    description="RAG-based AI Fashion Stylist Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include retailer router
from api.retailer_endpoints import router as retailer_router
app.include_router(retailer_router)

stylist_service = StylistService()
optimized_stylist_service = OptimizedStylistService()  # New optimized service
vector_store = VectorStore()
data_loader = DataLoader()

class HealthResponse(BaseModel):
    status: str
    version: str
    products_count: int

class StylistRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    occasion: Optional[str] = None
    budget: Optional[float] = None
    categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None
    max_results: Optional[int] = 20

class ProductSearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 20

class SimilarProductsRequest(BaseModel):
    product_id: str
    limit: Optional[int] = 10

@app.get("/", response_model=HealthResponse)
async def health_check():
    try:
        product_count = vector_store.collection.count() if vector_store.collection else 0
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            products_count=product_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/api/stylist/recommend")
async def get_recommendations(request: StylistRequest):
    try:
        user_query = UserQuery(
            query=request.query,
            user_id=request.user_id,
            occasion=request.occasion,
            budget=request.budget,
            preferred_categories=request.categories or [],
            excluded_categories=request.exclude_categories or [],
            max_results=request.max_results or 20
        )
        
        user_profile = None
        if request.user_id:
            user_profile = await _get_user_profile(request.user_id)
        
        response = await stylist_service.get_styling_recommendations(
            user_query,
            user_profile
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/stylist/recommend")
async def get_optimized_recommendations(request: StylistRequest):
    """
    Optimized recommendation endpoint with:
    - Query routing for greetings
    - Single LLM call
    - Caching support
    - Reduced latency
    """
    try:
        user_query = UserQuery(
            query=request.query,
            user_id=request.user_id,
            occasion=request.occasion,
            budget=request.budget,
            preferred_categories=request.categories or [],
            excluded_categories=request.exclude_categories or [],
            max_results=request.max_results or 20
        )
        
        user_profile = None
        if request.user_id:
            user_profile = await _get_user_profile(request.user_id)
        
        # Use optimized service
        response = await optimized_stylist_service.process_query(
            user_query,
            user_profile
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error getting optimized recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stylist/advice")
async def get_style_advice(query: str, user_id: Optional[str] = None):
    try:
        user_profile = None
        if user_id:
            user_profile = await _get_user_profile(user_id)
        
        advice = await stylist_service.get_style_advice(query, user_profile)
        
        return {"advice": advice}
        
    except Exception as e:
        logger.error(f"Error getting style advice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/stylist/advice")
async def get_optimized_style_advice(query: str, user_id: Optional[str] = None):
    """
    Optimized style advice with query routing
    """
    try:
        user_profile = None
        if user_id:
            user_profile = await _get_user_profile(user_id)
        
        # Use optimized service which handles greetings
        advice = await optimized_stylist_service.get_style_advice(query, user_profile)
        
        return {"advice": advice}
        
    except Exception as e:
        logger.error(f"Error getting optimized style advice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/search")
async def search_products(request: ProductSearchRequest):
    try:
        results = await vector_store.search(
            query=request.query,
            filters=request.filters,
            top_k=request.limit or 20
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/similar")
async def get_similar_products(request: SimilarProductsRequest):
    try:
        products = await stylist_service.get_similar_styles(
            request.product_id,
            request.limit or 10
        )
        
        return {"products": [p.dict() for p in products]}
        
    except Exception as e:
        logger.error(f"Error getting similar products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/outfit/{product_id}")
async def get_outfit_suggestions(product_id: str, user_id: Optional[str] = None):
    try:
        user_profile = None
        if user_id:
            user_profile = await _get_user_profile(user_id)
        
        outfits = await stylist_service.get_outfit_for_product(
            product_id,
            user_profile
        )
        
        return {"outfits": [o.dict() for o in outfits]}
        
    except Exception as e:
        logger.error(f"Error getting outfit suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/add")
async def add_product(product: Product):
    try:
        success = await vector_store.add_product(product)
        
        if success:
            return {"message": "Product added successfully", "product_id": product.product_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to add product")
            
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/bulk-upload")
async def bulk_upload_products(products: List[Product]):
    try:
        added_count = await vector_store.add_products_batch(products)
        
        return {
            "message": f"Successfully added {added_count} products",
            "count": added_count
        }
        
    except Exception as e:
        logger.error(f"Error bulk uploading products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/upload-csv")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are accepted")
        
        contents = await file.read()
        
        background_tasks.add_task(
            data_loader.process_csv_upload,
            contents,
            vector_store
        )
        
        return {
            "message": "CSV upload initiated",
            "filename": file.filename,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str):
    try:
        success = vector_store.delete_product(product_id)
        
        if success:
            return {"message": "Product deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
            
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/initialize")
async def initialize_sample_data():
    try:
        products = data_loader.load_sample_products()
        added_count = await vector_store.add_products_batch(products)
        
        return {
            "message": "Sample data initialized",
            "products_added": added_count
        }
        
    except Exception as e:
        logger.error(f"Error initializing sample data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/data/clear")
async def clear_all_data():
    try:
        success = vector_store.clear_all()
        
        if success:
            return {"message": "All data cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear data")
            
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _get_user_profile(user_id: str) -> Optional[UserProfile]:
    from models import UserProfile, StylePreference
    
    return UserProfile(
        user_id=user_id,
        style_preferences=StylePreference()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )