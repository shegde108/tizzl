#!/usr/bin/env python3
"""
Simplified test runner for Tizzl app - works with minimal dependencies
"""
import sys
import os
import logging

# Mock missing dependencies
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

# Mock ChromaDB classes
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
        return len(self.data)
    
    def add(self, *args, **kwargs):
        self.data.append(kwargs)
    
    def query(self, *args, **kwargs):
        return {
            "ids": [["MOCK_001", "MOCK_002"]],
            "metadatas": [[
                {"product_id": "MOCK_001", "name": "Mock Product 1", "price": 49.99},
                {"product_id": "MOCK_002", "name": "Mock Product 2", "price": 79.99}
            ]],
            "distances": [[0.1, 0.2]],
            "documents": [["Mock document 1", "Mock document 2"]]
        }
    
    def get(self, *args, **kwargs):
        return {"embeddings": [[0.1] * 384], "documents": ["Mock document"]}
    
    def delete(self, *args, **kwargs):
        pass

sys.modules['chromadb'].PersistentClient = MockPersistentClient
sys.modules['chromadb'].config = type(sys)('config')
sys.modules['chromadb'].config.Settings = lambda **kwargs: None

# Mock NumPy functions
class MockNumPy:
    @staticmethod
    def array(x):
        return x
    
    @staticmethod
    def random():
        class Random:
            @staticmethod
            def randn(n):
                return [0.5] * n
        return Random()
    
    class linalg:
        @staticmethod
        def norm(x):
            return 1.0

sys.modules['numpy'] = MockNumPy()
sys.modules['numpy'].random = MockNumPy.random()
sys.modules['numpy'].linalg = MockNumPy.linalg

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import the actual app
import uvicorn
from api.main import app

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Tizzl AI Stylist in TEST MODE")
    print("=" * 60)
    print("Running with mock data - no external dependencies needed")
    print("")
    print("Access the app at:")
    print("  - API: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("  - UI: http://localhost:8000/static/index.html")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    logging.basicConfig(level=logging.INFO)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )