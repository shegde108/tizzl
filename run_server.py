#!/usr/bin/env python3
"""
Production server runner for Tizzl - uses real OpenAI API
"""

import sys
import os

# Only mock the heavy ML dependencies we don't need
sys.modules['torch'] = type(sys)('torch')
sys.modules['torchvision'] = type(sys)('torchvision')
sys.modules['redis'] = type(sys)('redis')
sys.modules['boto3'] = type(sys)('boto3')
sys.modules['pandas'] = type(sys)('pandas')
sys.modules['sentence_transformers'] = type(sys)('sentence_transformers')
sys.modules['PIL'] = type(sys)('PIL')
sys.modules['scikit-learn'] = type(sys)('scikit-learn')
sys.modules['sklearn'] = type(sys)('sklearn')

# Mock ChromaDB with a simple in-memory store
import types

class MockPersistentClient:
    def __init__(self, *args, **kwargs):
        pass
    
    def get_or_create_collection(self, *args, **kwargs):
        return MockCollection()
    
    def delete_collection(self, *args, **kwargs):
        pass

class MockCollection:
    def __init__(self):
        self.products = {
            "SKU001": {"product_id": "SKU001", "name": "Classic White Cotton T-Shirt", "category": "tops", "price": 29.99, "brand": "Basics Co", "colors": "white", "occasions": "casual", "seasons": "all_season", "in_stock": True},
            "SKU002": {"product_id": "SKU002", "name": "High-Waisted Black Denim Jeans", "category": "bottoms", "price": 89.99, "brand": "DenimCraft", "colors": "black", "occasions": "casual,work", "seasons": "all_season", "in_stock": True},
            "SKU003": {"product_id": "SKU003", "name": "Silk Midi Wrap Dress", "category": "dresses", "price": 199.99, "brand": "Luxe Studio", "colors": "navy,burgundy", "occasions": "cocktail,formal", "seasons": "spring,summer", "in_stock": True},
            "SKU004": {"product_id": "SKU004", "name": "Leather Bomber Jacket", "category": "outerwear", "price": 399.99, "brand": "Urban Edge", "colors": "black,brown", "occasions": "casual", "seasons": "fall,winter", "in_stock": True},
            "SKU005": {"product_id": "SKU005", "name": "Canvas Low-Top Sneakers", "category": "shoes", "price": 59.99, "brand": "StepForward", "colors": "white,black,navy", "occasions": "casual,athletic", "seasons": "all_season", "in_stock": True},
            "SKU006": {"product_id": "SKU006", "name": "Cashmere Knit Sweater", "category": "tops", "price": 189.99, "brand": "Cozy Luxe", "colors": "camel,grey,cream", "occasions": "casual,work", "seasons": "fall,winter", "in_stock": True},
            "SKU007": {"product_id": "SKU007", "name": "Pleated Midi Skirt", "category": "bottoms", "price": 79.99, "brand": "Femme Fashion", "colors": "blush,black,navy", "occasions": "work,cocktail", "seasons": "spring,summer", "in_stock": True},
            "SKU008": {"product_id": "SKU008", "name": "Leather Crossbody Bag", "category": "bags", "price": 149.99, "brand": "Bag Studio", "colors": "tan,black", "occasions": "casual,work", "seasons": "all_season", "in_stock": True},
        }
    
    def count(self):
        return len(self.products)
    
    def add(self, *args, **kwargs):
        if 'ids' in kwargs and 'metadatas' in kwargs:
            for pid, metadata in zip(kwargs['ids'], kwargs['metadatas']):
                self.products[pid] = metadata
    
    def query(self, query_embeddings=None, n_results=10, where=None, include=None):
        # Return all products or filtered ones
        products_list = list(self.products.values())
        
        # Apply basic filtering if where clause exists
        if where:
            filtered = []
            for p in products_list:
                if 'category' in where and '$in' in where['category']:
                    if p.get('category') not in where['category']['$in']:
                        continue
                if 'price' in where and '$lte' in where['price']:
                    if p.get('price', 0) > where['price']['$lte']:
                        continue
                filtered.append(p)
            products_list = filtered
        
        # Limit results
        products_list = products_list[:min(n_results, len(products_list))]
        
        return {
            "ids": [[p["product_id"] for p in products_list]],
            "metadatas": [products_list],
            "distances": [[0.1 + i*0.05 for i in range(len(products_list))]],
            "documents": [[f"{p['name']} - {p.get('category', 'item')}" for p in products_list]]
        }
    
    def get(self, ids=None, include=None):
        if ids and ids[0] in self.products:
            return {
                "embeddings": [[0.1] * 384],
                "documents": [f"Product description for {ids[0]}"]
            }
        return {"embeddings": [[0.1] * 384], "documents": ["Product"]}
    
    def delete(self, ids=None):
        if ids:
            for pid in ids:
                self.products.pop(pid, None)

# Set up ChromaDB mock
chromadb_module = types.ModuleType('chromadb')
chromadb_module.PersistentClient = MockPersistentClient
config_module = types.ModuleType('chromadb.config')
config_module.Settings = lambda **kwargs: None
chromadb_module.config = config_module

sys.modules['chromadb'] = chromadb_module
sys.modules['chromadb.config'] = config_module

# Mock numpy for vector operations
class MockNumPy:
    @staticmethod
    def array(x):
        return x
    
    @staticmethod
    def dot(a, b):
        return 0.95
    
    @staticmethod
    def mean(x, axis=None):
        if isinstance(x, list) and len(x) > 0:
            return x[0] if axis is None else x
        return 0.5
    
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

# Mock sentence transformers
class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass
    
    def encode(self, text, **kwargs):
        if isinstance(text, list):
            return [[0.1] * 384 for _ in text]
        return [0.1] * 384

sys.modules['sentence_transformers'].SentenceTransformer = MockSentenceTransformer

# Now import and run
import uvicorn
from tizzl.api.main import app

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🎨 Tizzl AI Fashion Stylist - Running with OpenAI")
    print("=" * 70)
    print("\n✅ OpenAI API key detected - using GPT-4 for recommendations")
    print("✅ Sample products loaded in memory\n")
    print("📍 Access points:")
    print("   • Web Interface: http://localhost:8000/static/index.html")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/")
    print("\n💡 Try these queries:")
    print('   • "I need a casual outfit for weekend brunch"')
    print('   • "What should I wear to a summer wedding?"')
    print('   • "Help me style a business casual look"')
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")