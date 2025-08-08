# Tizzl Backend API Documentation

## Overview
Tizzl is an AI-powered fashion stylist backend service built with FastAPI that provides personalized outfit recommendations using advanced RAG (Retrieval-Augmented Generation) technology. The system combines semantic search, LLM-powered styling advice, and retailer integration to deliver intelligent fashion recommendations.

## Architecture

### Tech Stack
- **Framework**: FastAPI
- **Language**: Python 3.8+
- **Vector Database**: ChromaDB
- **AI Models**: OpenAI GPT-4/Anthropic Claude
- **Embeddings**: OpenAI text-embedding-3-small
- **Caching**: Redis (optional)
- **Testing**: pytest
- **Documentation**: OpenAPI/Swagger

### System Architecture
```
Frontend (React/Next.js)
         ↓
FastAPI Backend
    ├── API Layer (main.py, retailer_endpoints.py)
    ├── Service Layer
    │   ├── StylistService (recommendation orchestration)
    │   ├── RetrievalService (RAG pipeline)
    │   ├── LLMService (AI model interactions)
    │   └── RetailerRecommendationService (external integrations)
    ├── Core Layer
    │   ├── VectorStore (ChromaDB operations)
    │   ├── EmbeddingService (text vectorization)
    │   ├── Config (settings management)
    │   └── Prompts (prompt templates)
    └── Data Models (Pydantic schemas)
```

## Quick Start

### Server Setup
```bash
# Navigate to tizzl directory
cd tizzl

# Start the FastAPI server
python run.py
# OR
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Access endpoints at http://localhost:8000
# API docs at http://localhost:8000/docs
# Web interface at http://localhost:8000/static/index.html
```

### Environment Configuration
Create `.env` file in the tizzl directory:
```env
# Required for AI features
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Optional configurations
RETAILER_API_URL=https://api.retailer.com
RETAILER_API_KEY=...
CHROMA_PERSIST_DIRECTORY=./chroma_db
REDIS_URL=redis://localhost:6379
```

### Initial Data Setup
```bash
# Initialize with sample product data
curl -X POST http://localhost:8000/api/data/initialize
```

## API Endpoints

### Core Stylist Endpoints

#### GET `/` - Health Check
Returns API status and product count
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "products_count": 1250
}
```

#### POST `/api/stylist/recommend` - Get Style Recommendations
Main endpoint for AI-powered outfit recommendations.

**Request Body:**
```json
{
  "query": "I need a professional outfit for a job interview",
  "user_id": "user_123",
  "occasion": "work",
  "budget": 300.0,
  "categories": ["tops", "bottoms", "shoes"],
  "exclude_categories": ["athletic"],
  "max_results": 20
}
```

**Response:**
```json
{
  "response_id": "uuid-string",
  "user_query": "I need a professional outfit for a job interview",
  "recommendations": [
    {
      "outfit_id": "outfit-uuid",
      "name": "Professional Interview Look",
      "description": "A polished, confidence-inspiring outfit perfect for interviews",
      "items": [
        {
          "product": {
            "product_id": "product_123",
            "name": "Classic Blazer",
            "category": "outerwear",
            "price": 120.00,
            "sale_price": 96.00,
            "attributes": {
              "color": ["navy", "black"],
              "material": "wool blend",
              "brand": "Professional Wear Co."
            }
          },
          "styling_notes": "Perfect foundation piece",
          "role_in_outfit": "Layer"
        }
      ],
      "total_price": 285.50,
      "occasion": "work",
      "styling_tips": [
        "Pair with neutral accessories",
        "Ensure proper fit for professional appearance"
      ],
      "confidence_score": 0.92
    }
  ],
  "individual_items": [],
  "styling_advice": "For your job interview, focus on classic, well-fitted pieces...",
  "personalization_notes": "Recommendations tailored for professional settings",
  "processing_time_ms": 1250
}
```

#### POST `/api/stylist/advice` - Get Style Advice
Get general styling advice without product recommendations.

**Parameters:**
- `query` (string): Style question
- `user_id` (optional string): User identifier

**Response:**
```json
{
  "advice": "When choosing colors for your skin tone, consider warm vs cool undertones..."
}
```

### Product Management Endpoints

#### POST `/api/products/search` - Search Products
Semantic search through the product catalog.

**Request:**
```json
{
  "query": "red summer dress",
  "filters": {
    "category": "dresses",
    "price_max": 150,
    "in_stock": true
  },
  "limit": 20
}
```

#### POST `/api/products/similar` - Find Similar Products
Get products similar to a specific item.

**Request:**
```json
{
  "product_id": "dress_123",
  "limit": 10
}
```

#### POST `/api/products/outfit/{product_id}` - Get Outfit Suggestions
Build outfits around a specific product.

**URL Parameter:** `product_id`
**Query Parameter:** `user_id` (optional)

#### POST `/api/products/add` - Add Single Product
Add a new product to the catalog.

**Request:** Full Product object (see Data Models section)

#### POST `/api/products/bulk-upload` - Bulk Add Products
Upload multiple products at once.

**Request:** Array of Product objects

#### POST `/api/products/upload-csv` - CSV Upload
Upload products via CSV file (processed asynchronously).

**Request:** Multipart file upload

#### DELETE `/api/products/{product_id}` - Delete Product
Remove a product from the catalog.

### Data Management Endpoints

#### POST `/api/data/initialize` - Initialize Sample Data
Populate the system with sample product data for testing.

#### DELETE `/api/data/clear` - Clear All Data
Remove all products from the vector database.

### Retailer Integration Endpoints

#### POST `/api/retailer/recommendations` - Get Retailer Recommendations
Get recommendations from external retailer systems based on user interactions.

**Request:**
```json
{
  "product_id": "item_123",
  "user_id": "user_456",
  "interaction_type": "click",
  "session_id": "session_789",
  "context": {
    "page": "stylist_chat",
    "query": "summer outfit"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "recommendations": [
    {
      "product_id": "recommended_item_1",
      "name": "Complementary Summer Top",
      "price": 45.99,
      "score": 0.89,
      "reason": "Frequently bought together",
      "styling_notes": "Perfect complement to your selected item"
    }
  ],
  "metadata": {
    "source": "retailer_api",
    "interaction_recorded": true
  }
}
```

#### POST `/api/retailer/recommendations/batch` - Batch Recommendations
Process multiple interactions and get aggregated recommendations.

**Request:**
```json
{
  "interactions": [
    {
      "product_id": "item_1",
      "user_id": "user_123",
      "interaction_type": "like",
      "session_id": "session_456"
    }
  ],
  "create_outfit": true
}
```

#### GET `/api/retailer/interactions/history` - Interaction History
Get user's interaction history.

**Query Parameters:**
- `session_id` (optional): Filter by session
- `user_id` (optional): Filter by user

#### POST `/api/retailer/outfit/from-interactions` - Create Outfit from Interactions
Build outfits from previously interacted products.

**Request:**
```json
{
  "product_ids": ["item_1", "item_2", "item_3"],
  "user_id": "user_123"
}
```

#### POST `/api/retailer/feedback` - Submit Feedback
Provide feedback on recommendations for ML improvement.

**Request:**
```json
{
  "product_id": "recommended_item",
  "feedback_type": "helpful",
  "user_id": "user_123",
  "notes": "Great recommendation, purchased!"
}
```

## Data Models

### Product Model
Core product entity with rich attributes for fashion items.

```python
class Product(BaseModel):
    product_id: str                    # Unique identifier
    name: str                         # Product name
    category: Category                # Enum: tops, bottoms, dresses, etc.
    subcategory: Optional[str]        # More specific categorization
    description: str                  # Product description
    attributes: ProductAttribute      # Detailed attributes
    price: float                      # Original price
    sale_price: Optional[float]       # Discounted price
    currency: str = "USD"            # Currency code
    sizes: List[str]                 # Available sizes
    in_stock: bool = True            # Inventory status
    images: List[str]                # Image URLs
    url: Optional[str]               # Product page URL
    embeddings: Optional[ProductEmbedding]  # Vector embeddings
    metadata: Dict[str, Any]         # Additional data
    created_at: datetime
    updated_at: datetime
```

### ProductAttribute Model
Detailed product characteristics for fashion items.

```python
class ProductAttribute(BaseModel):
    color: List[str]                 # Available colors
    pattern: Optional[str]           # Pattern type (solid, striped, etc.)
    material: Optional[str]          # Fabric composition
    occasion: List[Occasion]         # Suitable occasions
    season: List[Season]             # Appropriate seasons
    style: Optional[str]             # Style descriptor
    brand: Optional[str]             # Brand name
    fit: Optional[str]               # Fit type (slim, regular, etc.)
    care_instructions: Optional[str] # Care guide
```

### User Models

#### UserProfile
Complete user profile for personalization.

```python
class UserProfile(BaseModel):
    user_id: str
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    body_type: Optional[BodyType]    # Enum: pear, apple, hourglass, etc.
    height: Optional[float]          # Height in cm
    weight: Optional[float]          # Weight in kg
    sizes: Dict[str, str]            # Size mappings by category
    style_preferences: StylePreference
    budget_min: Optional[float]
    budget_max: Optional[float]
    location: Optional[str]
    purchase_history: List[str]      # Product IDs
    wishlist: List[str]              # Product IDs
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

#### UserQuery
Query structure for style recommendations.

```python
class UserQuery(BaseModel):
    query: str                       # Natural language query
    user_id: Optional[str]
    occasion: Optional[str]          # Specific occasion
    budget: Optional[float]          # Budget constraint
    preferred_categories: List[str]  # Preferred product categories
    excluded_categories: List[str]   # Categories to avoid
    color_preferences: List[str]     # Preferred colors
    size_filters: Dict[str, str]     # Size constraints
    include_sale_items: bool = True  # Include discounted items
    max_results: int = 20           # Maximum results
    conversation_id: Optional[str]   # Chat session ID
    context: Optional[Dict[str, Any]] # Additional context
```

### Response Models

#### StylistResponse
Main response structure for styling recommendations.

```python
class StylistResponse(BaseModel):
    response_id: str
    user_query: str
    recommendations: List[OutfitRecommendation]  # Complete outfits
    individual_items: List[Product]              # Individual pieces
    styling_advice: str                          # AI-generated advice
    personalization_notes: Optional[str]         # User-specific notes
    alternative_options: List[Dict[str, Any]]    # Alternative suggestions
    metadata: Dict[str, Any]                     # Processing metadata
    created_at: datetime
    processing_time_ms: Optional[int]            # Response time
```

#### OutfitRecommendation
Complete outfit with styling guidance.

```python
class OutfitRecommendation(BaseModel):
    outfit_id: str
    name: str                        # Outfit name
    description: str                 # Outfit description
    items: List[OutfitItem]         # Component products
    total_price: float              # Combined price
    occasion: Optional[str]         # Suitable occasion
    season: Optional[str]           # Appropriate season
    styling_tips: List[str]         # Styling advice
    confidence_score: float         # AI confidence (0-1)
    reasoning: Optional[str]        # Why this outfit works
```

#### OutfitItem
Individual item within an outfit.

```python
class OutfitItem(BaseModel):
    product: Product                # The product details
    styling_notes: Optional[str]    # How to style this item
    role_in_outfit: str            # Role (top, bottom, layer, etc.)
```

## Configuration

### Settings Management
Configuration is handled through Pydantic Settings with `.env` file support.

```python
# core/config.py
class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Database
    chroma_persist_directory: str = "./chroma_db"
    redis_url: str = "redis://localhost:6379"
    
    # AI Model Settings
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Vector Search
    embedding_dimension: int = 1536
    similarity_threshold: float = 0.7
    rerank_top_k: int = 50
    final_top_k: int = 15
    
    # API Configuration
    api_cors_origins: list = ["*"]
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    # Performance
    max_items_per_query: int = 20
    cache_ttl: int = 3600
    enable_cache: bool = True
```

### Environment Variables
```bash
# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Retailer Integration
RETAILER_API_URL=https://api.retailer.com
RETAILER_API_KEY=...

# Database
CHROMA_PERSIST_DIRECTORY=./chroma_db
REDIS_URL=redis://localhost:6379

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=["http://localhost:3000", "https://your-frontend.com"]
```

## RAG Pipeline

### Retrieval Process
1. **Query Enhancement**: LLM extracts searchable terms from natural language
2. **Embedding Generation**: Convert query to vector representation
3. **Hybrid Search**: Combine semantic similarity with metadata filtering
4. **Reranking**: LLM scores and reorders results by relevance
5. **Business Rules**: Apply inventory, pricing, and personalization filters

### Vector Store Operations
- **ChromaDB**: Persistent vector database for product embeddings
- **Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **Similarity Search**: Cosine similarity with configurable threshold
- **Metadata Filtering**: Pre-filter by category, price, availability

### Prompt Engineering
Centralized prompt templates in `core/prompts.py`:
- **Outfit Generation**: Creates complete outfit recommendations
- **Style Advice**: Provides general fashion guidance
- **Query Enhancement**: Extracts search terms from user queries
- **Product Reranking**: Scores products by relevance
- **Outfit Compatibility**: Evaluates item combinations

## Authentication & Security

### API Security
- **CORS**: Configurable origins for cross-domain requests
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Structured exception handling with appropriate HTTP codes
- **Request Size Limits**: Built-in FastAPI request size limitations

### Data Protection
- **Environment Variables**: Sensitive data stored in `.env` files
- **API Key Management**: Secure handling of external service keys
- **Logging**: Structured logging without sensitive data exposure

### Rate Limiting
Production deployments should implement:
- API rate limiting per client/IP
- Resource usage monitoring
- Request timeout configurations

## Testing

### Test Structure
```bash
# Run all tests
cd tizzl
pytest tests/ -v

# Test categories
pytest tests/ -m unit -v          # Unit tests
pytest tests/ -m api -v           # API endpoint tests
pytest tests/ -m integration -v   # Integration tests

# Coverage reporting
pytest tests/test_retailer_*.py --cov=tizzl.services.retailer_integration --cov-report=term-missing

# Specific test execution
pytest tests/test_retailer_integration.py::TestRetailerRecommendationService::test_get_retailer_recommendations_click -v
```

### Test Configuration
- **pytest**: Test framework with async support
- **Fixtures**: Shared test data in `tests/conftest.py`
- **Mocking**: External service mocking for isolated testing
- **Coverage**: Code coverage reporting for quality assurance

## Frontend Integration

### API Integration
The backend provides RESTful APIs that can be consumed by any frontend framework:

```javascript
// Example React integration
const getRecommendations = async (query) => {
  const response = await fetch('http://localhost:8000/api/stylist/recommend', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      user_id: getCurrentUserId(),
      max_results: 20
    })
  });
  
  return response.json();
};

// Handle retailer interactions
const recordInteraction = async (productId, interactionType) => {
  await fetch('http://localhost:8000/api/retailer/recommendations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      product_id: productId,
      user_id: getCurrentUserId(),
      interaction_type: interactionType,
      session_id: getSessionId()
    })
  });
};
```

### WebSocket Support
For real-time features, consider implementing WebSocket endpoints:
- Live styling advice during browsing
- Real-time outfit building
- Instant recommendation updates

### Frontend Requirements
- **CORS Configuration**: Ensure frontend domain is in `API_CORS_ORIGINS`
- **Authentication**: Implement user session management
- **Error Handling**: Handle API errors gracefully
- **Loading States**: Show progress during AI processing
- **Image Optimization**: Handle product image loading

## Deployment

### Production Configuration
```bash
# Production environment
ENVIRONMENT=production
LOG_LEVEL=WARNING
API_HOST=0.0.0.0
API_PORT=8000

# Security
API_CORS_ORIGINS=["https://your-domain.com"]

# Performance
ENABLE_CACHE=true
CACHE_TTL=3600
MAX_ITEMS_PER_QUERY=50
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY tizzl/ ./tizzl/
WORKDIR /app/tizzl

EXPOSE 8000
CMD ["python", "run.py"]
```

### Health Monitoring
- Use the `/` endpoint for health checks
- Monitor processing times in responses
- Track vector database performance
- Monitor external API response times

## Performance Optimization

### Caching Strategy
- **Redis**: Cache frequent queries and results
- **Vector Search**: Cache embeddings and similarity results
- **LLM Responses**: Cache common styling advice

### Database Optimization
- **ChromaDB**: Optimize collection size and indexing
- **Embeddings**: Batch processing for bulk operations
- **Metadata**: Efficient filtering strategies

### Scaling Considerations
- **Horizontal Scaling**: Multiple FastAPI instances
- **Load Balancing**: Distribute requests across instances
- **Async Processing**: Background tasks for heavy operations
- **Database Sharding**: Partition large product catalogs

## Troubleshooting

### Common Issues

#### API Key Configuration
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Verify in logs
tail -f logs/app.log | grep "API key"
```

#### Vector Database Issues
```bash
# Clear and reinitialize ChromaDB
curl -X DELETE http://localhost:8000/api/data/clear
curl -X POST http://localhost:8000/api/data/initialize
```

#### Memory Issues
- Monitor ChromaDB memory usage
- Implement product pagination
- Use batch processing for large uploads

#### Performance Debugging
- Check processing times in response metadata
- Monitor LLM API response times
- Profile vector search performance

### Logging
Structured logging is available at multiple levels:
- `DEBUG`: Detailed processing information
- `INFO`: General application flow
- `WARNING`: Potential issues
- `ERROR`: Actual errors and exceptions

## Future Enhancements

### Planned Features
- **Visual Search**: Image-based product search
- **Size Recommendations**: ML-powered size suggestions
- **Trend Analysis**: Fashion trend integration
- **Social Features**: User-generated content integration
- **Multi-language**: International market support

### Technical Improvements
- **GraphQL**: Alternative API interface
- **Microservices**: Service decomposition
- **Event Streaming**: Real-time data processing
- **ML Pipelines**: Custom recommendation models
- **A/B Testing**: Experiment framework

This documentation provides comprehensive coverage of the Tizzl backend system, enabling seamless frontend integration and future development.



Message Flow

  1. Frontend (static/index.html:264-275)
  - User types message and clicks "Get Recommendations" or presses Enter
  - JavaScript getRecommendations() function triggers
  - Makes POST request to /api/stylist/recommend with query, occasion, and budget

  2. API Layer (api/main.py:75-101)
  - FastAPI receives POST at /api/stylist/recommend
  - Creates UserQuery object from request data
  - Optionally gets user profile (if user_id provided)
  - Calls stylist_service.get_styling_recommendations()

  3. Stylist Service (services/stylist_service.py:20-56)
  - Orchestrates the main recommendation flow
  - Calls retrieval_service.retrieve_products() to find matching products
  - If products found, calls llm_service.generate_outfit_recommendations()
  - Parses LLM response into structured outfit recommendations
  - Returns StylistResponse with outfits, styling advice, and metadata

  4. Retrieval Service (services/retrieval_service.py)
  - Enhances user query using LLM to extract search terms
  - Builds filters from user preferences (category, price, occasion)
  - Calls vector_store.search() for semantic search
  - Reranks results using LLM for relevance
  - Applies business rules (stock status, budget limits)

  5. Vector Store (core/vector_store.py:105-145)
  - Creates embedding of search query
  - Queries ChromaDB with semantic similarity + metadata filters
  - Returns ranked product results with similarity scores

  6. LLM Service (services/llm_service.py:27-43)
  - Generates outfit recommendations using configured AI provider (OpenAI/Anthropic/Mock)
  - Uses prompts from core/prompts.py
  - Returns styled text response with outfit suggestions

  7. Response Processing (services/stylist_service.py:104-150)
  - Parses LLM response text to extract outfit structures
  - Maps mentioned products to actual product objects
  - Creates OutfitRecommendation objects with items, prices, tips

  8. API Response (api/main.py:97)
  - Returns JSON response with recommendations, advice, processing time

  9. Frontend Display (static/index.html:314-378)
  - JavaScript receives JSON response
  - Dynamically creates HTML cards for each outfit
  - Displays product names, prices, and styling tips
  - Shows results to user


--------
  Detailed Flow: 
  example query from user: "i want to find a top that goes well with a silk white skirt"

  Step 3: Stylist Service (services/stylist_service.py:20-56)

  Input Processing:
  user_query = UserQuery(
      query="i want to find a top that goes well with a silk white skirt",
      user_id=None,
      occasion=None,
      budget=None,
      preferred_categories=[],
      excluded_categories=[],
      max_results=20
  )

  Main Flow:
  1. Line 28: Calls retrieval_service.retrieve_products(user_query, user_profile)
  2. Line 33: Calls llm_service.generate_outfit_recommendations() with the query and retrieved products
  3. Line 40: Parses LLM response into structured outfit objects

  Step 4: Retrieval Service - Deep Dive (services/retrieval_service.py:18-48)

  4.1 Query Enhancement (Line 24):
  enhanced_terms = await self.llm_service.enhance_search_query(query.query)

  The LLM receives prompt from core/prompts.py:81-94:
  Extract and enhance search keywords from: "i want to find a top that goes well with a silk white skirt"

  Identify:
  1. Specific product types: top, blouse, shirt
  2. Colors/materials: white, neutral colors, silk-compatible fabrics
  3. Occasions: elegant, sophisticated, versatile
  4. Style preferences: coordinating, complementary, refined
  5. Implicit requirements: formal-casual balance, texture mixing

  Enhanced terms might include:
  - "blouse", "shirt", "sweater", "cardigan"
  - "white", "cream", "navy", "black", "neutral"
  - "silk", "cotton", "chiffon", "knit"
  - "elegant", "sophisticated", "refined"

  4.2 Combined Query (Line 26):
  combined_query = "i want to find a top that goes well with a silk white skirt blouse shirt sweater neutral elegant sophisticated silk 
  cotton chiffon"

  4.3 Filter Building (Line 28):
  filters = self._build_filters(query)
  # Results in: {"in_stock": True} since no budget/categories specified

  4.4 Vector Store Search (Lines 30-34):
  search_results = await self.vector_store.search(
      query=combined_query,
      filters={"in_stock": True},
      top_k=50  # settings.rerank_top_k
  )

  Step 5: Vector Store Search Mechanics (core/vector_store.py:105-145)

  5.1 Embedding Creation (Line 112):
  query_embedding = await self.embedding_service.create_embedding(combined_query)
  - Converts the enhanced text query into a 1536-dimension vector (OpenAI) or 1024-dimension (other models)
  - Captures semantic meaning: "top + silk + white + elegant + sophisticated"

  5.2 ChromaDB Query (Lines 125-135):
  collection_count = self.collection.count()  # Check if empty (our previous fix)
  if collection_count == 0:
      return []  # Prevents the error you saw

  results = self.collection.query(
      query_embeddings=[query_embedding],
      n_results=min(50, collection_count),
      where={"in_stock": True},  # Only in-stock items
      include=["metadatas", "distances", "documents"]
  )

  5.3 ChromaDB Semantic Matching:
  - Searches through embedded product descriptions looking for semantic similarity
  - Example products that would rank highly:
    - "Elegant silk blouse in cream" (high similarity: silk + elegant)
    - "Classic white button-down shirt" (medium-high: white + classic)
    - "Soft cashmere sweater in ivory" (medium: soft texture + neutral color)
    - "Navy blue cotton blouse" (medium: complementary color + formal)

  5.4 Results Formatting (Lines 132-142):
  formatted_results = []
  for i in range(len(results["ids"][0])):
      formatted_results.append({
          "product_id": results["ids"][0][i],
          "metadata": results["metadatas"][0][i],
          "distance": results["distances"][0][i],  # Lower = more similar
          "document": results["documents"][0][i]   # Original product text
      })

  Example Results:
  [
      {
          "product_id": "TOP_001",
          "metadata": {"name": "Silk Cream Blouse", "category": "tops", "price": 89.99, "colors": "cream,white"},
          "distance": 0.15,  # Very similar
          "document": "Elegant silk blouse in cream perfect for sophisticated occasions..."
      },
      {
          "product_id": "TOP_002",
          "metadata": {"name": "Classic White Shirt", "category": "tops", "price": 65.00, "colors": "white"},
          "distance": 0.23,  # Similar
          "document": "Classic white cotton button-down shirt versatile for work or casual..."
      }
  ]

  Back to Step 4: Retrieval Service Completion

  4.5 Product Loading (Line 36):
  products = await self._load_products(search_results)
  - Converts metadata dictionaries into full Product objects
  - Uses _fetch_product() method (lines 132-160)

  4.6 Reranking (Lines 38-41):
  if len(products) > 20:  # settings.final_top_k
      product_ids = await self.llm_service.rerank_products(query.query, products)
      products = self._reorder_products(products, product_ids)
      products = products[:20]

  Reranking Process:
  - LLM receives original query + all found products
  - Analyzes which products best answer "top that goes well with silk white skirt"
  - Returns ranked list of product IDs based on styling compatibility
  - Products reordered by this ranking

  4.7 Business Rules (Line 43):
  products = self._apply_business_rules(products, query)
  - Filters out excluded categories (none in this case)
  - Removes items over budget (none specified)
  - Applies color preferences (none specified)

    The process returns a ranked list of Product objects that semantically match "tops that go well with silk white skirt", prioritizing
  items that complement the elegance, color palette, and sophistication implied by a silk white skirt.

  The key insight is that this is a hybrid retrieval system:
  1. Semantic search finds products with similar meaning/style
  2. Metadata filtering ensures practical constraints (stock, budget)
  3. LLM reranking applies fashion expertise for final ordering
  4. Business rules apply final filters based on user constraints

  This multi-stage approach ensures both semantic relevance and practical applicability for the styling recommendations.