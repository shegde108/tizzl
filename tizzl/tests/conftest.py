import pytest
import asyncio
from typing import Generator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_product_data():
    """Provide sample product data for testing"""
    return {
        "product_id": "TEST_PRODUCT_001",
        "name": "Classic White T-Shirt",
        "category": "tops",
        "description": "A versatile white cotton t-shirt",
        "price": 29.99,
        "attributes": {
            "color": ["white"],
            "material": "cotton",
            "occasion": ["casual"],
            "season": ["all_season"],
            "style": "classic"
        }
    }

@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing"""
    return {
        "user_id": "test_user_123",
        "name": "Test User",
        "style_preferences": {
            "preferred_colors": ["blue", "white", "black"],
            "style_personalities": ["classic", "minimalist"],
            "preferred_fit": "regular"
        },
        "budget_max": 200.0
    }

@pytest.fixture
def sample_interaction_data():
    """Provide sample interaction data for testing"""
    return {
        "product_id": "PROD_001",
        "user_id": "user_123",
        "interaction_type": "click",
        "session_id": "session_456",
        "context": {
            "categories": ["tops"],
            "price_range": {"min": 20, "max": 100}
        }
    }