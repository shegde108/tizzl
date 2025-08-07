#!/usr/bin/env python3
"""
Test runner for Tizzl app - runs with minimal dependencies and mock data
"""
import sys
import os

# Mock missing heavy dependencies
sys.modules['chromadb'] = type(sys)('chromadb')
sys.modules['openai'] = type(sys)('openai')
sys.modules['anthropic'] = type(sys)('anthropic')
sys.modules['sentence_transformers'] = type(sys)('sentence_transformers')
sys.modules['torch'] = type(sys)('torch')
sys.modules['torchvision'] = type(sys)('torchvision')
sys.modules['redis'] = type(sys)('redis')
sys.modules['boto3'] = type(sys)('boto3')
sys.modules['pandas'] = type(sys)('pandas')
sys.modules['numpy'] = type(sys)('numpy')
sys.modules['sklearn'] = type(sys)('sklearn')
sys.modules['PIL'] = type(sys)('PIL')
sys.modules['scikit-learn'] = type(sys)('scikit-learn')

# Mock ChromaDB
class MockPersistentClient:
    def __init__(self, *args, **kwargs):
        pass
    
    def get_or_create_collection(self, *args, **kwargs):
        return MockCollection()
    
    def delete_collection(self, *args, **kwargs):
        pass

class MockCollection:
    def __init__(self):
        self.data = []
    
    def count(self):
        return 10  # Pretend we have 10 products
    
    def add(self, *args, **kwargs):
        self.data.append(kwargs)
    
    def query(self, *args, **kwargs):
        # Always return some products for any query
        return {
            "ids": [["SKU001", "SKU002", "SKU003", "SKU005", "SKU008"]],
            "metadatas": [[
                {"product_id": "SKU001", "name": "Classic White Cotton T-Shirt", "category": "tops", "price": 29.99, "brand": "Basics Co", "colors": "white", "occasions": "casual", "seasons": "all_season", "in_stock": True},
                {"product_id": "SKU002", "name": "High-Waisted Black Denim Jeans", "category": "bottoms", "price": 89.99, "brand": "DenimCraft", "colors": "black", "occasions": "casual,work", "seasons": "all_season", "in_stock": True},
                {"product_id": "SKU003", "name": "Silk Midi Wrap Dress", "category": "dresses", "price": 199.99, "brand": "Luxe Studio", "colors": "navy,burgundy", "occasions": "cocktail,formal", "seasons": "spring,summer", "in_stock": True},
                {"product_id": "SKU005", "name": "Canvas Low-Top Sneakers", "category": "shoes", "price": 59.99, "brand": "StepForward", "colors": "white,black,navy", "occasions": "casual,athletic", "seasons": "all_season", "in_stock": True},
                {"product_id": "SKU008", "name": "Leather Crossbody Bag", "category": "bags", "price": 149.99, "brand": "Bag Studio", "colors": "tan,black", "occasions": "casual,work", "seasons": "all_season", "in_stock": True}
            ]],
            "distances": [[0.1, 0.12, 0.15, 0.18, 0.2]],
            "documents": [["Classic white cotton t-shirt perfect for layering", "High-waisted black denim jeans with stretch", "Elegant silk midi dress with wrap silhouette", "Comfortable canvas sneakers", "Compact leather crossbody bag"]]
        }
    
    def get(self, *args, **kwargs):
        return {"embeddings": [[0.1] * 384], "documents": ["Mock product description"]}
    
    def delete(self, *args, **kwargs):
        pass

# Create mock chromadb module with proper structure
import types
chromadb_module = types.ModuleType('chromadb')
chromadb_module.PersistentClient = MockPersistentClient

# Create config submodule
config_module = types.ModuleType('chromadb.config')
config_module.Settings = lambda **kwargs: None
chromadb_module.config = config_module

sys.modules['chromadb'] = chromadb_module
sys.modules['chromadb.config'] = config_module

# Mock NumPy
class MockNumPy:
    @staticmethod
    def array(x):
        return x
    
    @staticmethod
    def dot(a, b):
        return 0.95
    
    @staticmethod
    def mean(x, axis=None):
        return x[0] if isinstance(x, list) and len(x) > 0 else 0.5
    
    @staticmethod
    def sum(x, axis=None):
        return sum(x) if isinstance(x, list) else x
    
    class linalg:
        @staticmethod
        def norm(x):
            return 1.0
    
    class random:
        @staticmethod
        def randn(n):
            return [0.5] * n

mock_numpy = MockNumPy()
mock_numpy.linalg = MockNumPy.linalg
mock_numpy.random = MockNumPy.random
sys.modules['numpy'] = mock_numpy

# Mock OpenAI
class MockOpenAI:
    class OpenAI:
        def __init__(self, *args, **kwargs):
            self.embeddings = self.Embeddings()
            self.chat = self.Chat()
        
        class Embeddings:
            class EmbeddingResponse:
                def __init__(self):
                    self.data = [type('obj', (object,), {'embedding': [0.1] * 1536})]
            
            def create(self, *args, **kwargs):
                return self.EmbeddingResponse()
        
        class Chat:
            class Completions:
                class Response:
                    class Choice:
                        class Message:
                            content = "This is a great outfit combination! The white t-shirt pairs perfectly with black jeans for a classic casual look."
                        message = Message()
                    choices = [Choice()]
                
                def create(self, *args, **kwargs):
                    return self.Response()
            
            completions = Completions()

sys.modules['openai'].OpenAI = MockOpenAI.OpenAI
sys.modules['openai'].api_key = None

# Mock Sentence Transformers
class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass
    
    def encode(self, text, **kwargs):
        if isinstance(text, list):
            return [[0.1] * 384 for _ in text]
        return [0.1] * 384

sys.modules['sentence_transformers'].SentenceTransformer = MockSentenceTransformer

# Now run the app
import uvicorn
from tizzl.api.main import app

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🎨 Starting Tizzl AI Fashion Stylist - TEST MODE")
    print("=" * 70)
    print("\n✅ Running with mock data - no external APIs needed")
    print("✅ All recommendations will use sample products\n")
    print("📍 Access points:")
    print("   • Web Interface: http://localhost:8000/static/index.html")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/")
    print("\n💡 Test the app by:")
    print("   1. Opening the web interface")
    print("   2. Click 'Load Sample Products'")
    print("   3. Try queries like 'casual outfit for summer'")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")