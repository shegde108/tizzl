# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Start the FastAPI server
cd tizzl
python run.py

# Alternative: Run with uvicorn directly
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Access the web interface
open http://localhost:8000/static/index.html
```

### Testing
```bash
# Run all tests with verbose output
cd tizzl
pytest tests/ -v

# Run specific test categories
pytest tests/ -m unit -v                    # Unit tests only
pytest tests/ -m api -v                     # API endpoint tests
pytest tests/ -m integration -v             # Integration tests

# Run with coverage
pytest tests/test_retailer_*.py --cov=tizzl.services.retailer_integration --cov-report=term-missing

# Run a single test file
pytest tests/test_retailer_integration.py -v

# Run a single test function
pytest tests/test_retailer_integration.py::TestRetailerRecommendationService::test_get_retailer_recommendations_click -v
```

### Development Setup
```bash
# Install dependencies
pip install -r tizzl/requirements.txt

# Copy and configure environment variables
cp tizzl/.env.example tizzl/.env
# Edit .env to add API keys for OpenAI or Anthropic

# Initialize sample data (after starting server)
curl -X POST http://localhost:8000/api/data/initialize
```

## Architecture Overview

### Core RAG Pipeline
The system implements a sophisticated Retrieval-Augmented Generation pipeline:

1. **Query Enhancement**: User queries are enriched using LLM to extract search terms
2. **Hybrid Retrieval**: Combines semantic search (via embeddings) with metadata filtering
3. **Reranking**: Retrieved products are reranked by relevance using LLM
4. **Response Generation**: LLM generates personalized outfit recommendations with styling advice

### Service Layer Architecture
```
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ├── StylistService (orchestrates recommendations)
    ├── RetrievalService (manages RAG pipeline)
    ├── LLMService (handles AI model interactions)
    └── RetailerRecommendationService (integrates external systems)
    ↓
Core Layer (Infrastructure)
    ├── VectorStore (ChromaDB operations)
    ├── EmbeddingService (text → vectors)
    └── PromptTemplates (prompt engineering)
```

### Key Design Patterns

**Dependency Injection Flow**: Services are instantiated at module level and injected into endpoints. Configuration comes from `core/config.py` which uses Pydantic settings with `.env` file support.

**Async Throughout**: All service methods are async, enabling non-blocking I/O. The pattern is consistent: `async def method_name() -> ReturnType`.

**Model-First Design**: All data structures are defined as Pydantic models in `models/` directory. This ensures type safety and automatic validation.

**Fallback Strategy**: The system gracefully degrades when external services are unavailable:
- No OpenAI/Anthropic key → Uses mock responses
- No retailer API → Generates deterministic mock recommendations
- Missing embeddings → Creates random embeddings as fallback

### Retailer Integration Architecture

The retailer integration (`services/retailer_integration.py` + `api/retailer_endpoints.py`) tracks user interactions and bridges between AI styling and retailer's recommendation engine:

1. **Interaction Recording**: Every click/like/cart action is tracked with session context
2. **External API Call**: Fetches recommendations from retailer's system (if configured)
3. **Enhancement**: Adds styling notes and outfit potential scores
4. **Response Aggregation**: Combines and deduplicates recommendations from multiple interactions

### Vector Store Strategy

ChromaDB is used for semantic search with the following approach:
- **Embedding Generation**: Products are converted to text descriptions then embedded
- **Metadata Filtering**: Pre-filters by category, price, stock status before semantic search
- **Collection Management**: Single "products" collection with structured metadata

### Prompt Engineering

Prompts are centralized in `core/prompts.py` with specialized templates for:
- Outfit recommendations (considers inventory, user profile, context)
- Style advice (general fashion guidance)
- Query enhancement (extracts search terms)
- Product reranking (sorts by relevance)
- Outfit compatibility (evaluates item combinations)

## Critical Files and Their Relationships

### Entry Points
- `run.py`: Application starter that configures and launches Uvicorn
- `api/main.py`: FastAPI app definition and endpoint registration

### Configuration Chain
1. `.env` file (user-provided API keys and settings)
2. `core/config.py` loads via Pydantic BaseSettings
3. Settings object injected throughout application

### Service Dependencies
- `StylistService` depends on `RetrievalService` and `LLMService`
- `RetrievalService` depends on `VectorStore`, `EmbeddingService`, and `LLMService`
- `VectorStore` depends on `EmbeddingService`
- All services depend on `core/config.settings`

### Test Structure
- `tests/conftest.py`: Pytest configuration and shared fixtures
- `tests/pytest.ini`: Test discovery and marker configuration
- Test files mirror source structure (e.g., `test_retailer_integration.py` tests `services/retailer_integration.py`)

## Environment Variables

Required for full functionality:
```
OPENAI_API_KEY=sk-...           # For GPT-4 embeddings and generation
ANTHROPIC_API_KEY=sk-ant-...    # Alternative to OpenAI
```

Optional configuration:
```
RETAILER_API_URL=https://api.retailer.com  # External retailer API
RETAILER_API_KEY=...                        # Retailer API authentication
CHROMA_PERSIST_DIRECTORY=./chroma_db       # Vector DB storage location
REDIS_URL=redis://localhost:6379           # Cache configuration
```

## Common Development Tasks

### Adding a New Endpoint
1. Define request/response models in `models/`
2. Implement business logic in appropriate service under `services/`
3. Add endpoint to `api/main.py` or create new router
4. Write tests in `tests/` following existing patterns

### Modifying the RAG Pipeline
The retrieval pipeline is in `services/retrieval_service.py`. Key methods:
- `retrieve_products()`: Main retrieval orchestration
- `_build_filters()`: Constructs metadata filters
- `_reorder_products()`: Applies reranking
- `_apply_business_rules()`: Final filtering logic

### Extending LLM Integration
LLM interactions are centralized in `services/llm_service.py`. To add new LLM provider:
1. Add provider client initialization in `__init__()`
2. Implement `_generate_{provider}_response()` method
3. Update `_generate_response()` to route to new provider

### Working with Vector Store
Vector operations are in `core/vector_store.py`. Key operations:
- `add_product()`: Index single product
- `add_products_batch()`: Bulk indexing
- `search()`: Semantic search with filters
- `get_similar_products()`: Find similar items

## Testing Patterns

### Mocking External Services
```python
from unittest.mock import AsyncMock, patch

@patch('tizzl.services.llm_service.openai')
async def test_with_mock(mock_openai):
    mock_openai.chat.completions.create = AsyncMock(return_value=...)
```

### Testing Async Functions
All async tests use `@pytest.mark.asyncio` decorator and `async def test_...()` pattern.

### Fixture Usage
Common fixtures are in `tests/conftest.py`:
- `sample_product_data`: Product test data
- `sample_user_data`: User profile test data
- `sample_interaction_data`: Interaction test data