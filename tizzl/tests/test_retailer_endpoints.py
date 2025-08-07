import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from api.main import app
from services.retailer_integration import RetailerRecommendationService

client = TestClient(app)

class TestRetailerEndpoints:
    """Test suite for retailer recommendation API endpoints"""
    
    @pytest.fixture
    def mock_retailer_service(self):
        """Create a mock retailer service"""
        with patch('api.retailer_endpoints.retailer_service') as mock:
            yield mock
    
    def test_get_product_recommendations(self, mock_retailer_service):
        """Test single product recommendation endpoint"""
        # Mock the service response
        mock_retailer_service.get_retailer_recommendations = AsyncMock(return_value={
            "status": "success",
            "interaction": {
                "product_id": "PROD_001",
                "user_id": "user_123",
                "type": "click",
                "session_id": "session_456"
            },
            "recommendations": [
                {
                    "product_id": "REC_001",
                    "name": "Recommended Item 1",
                    "score": 0.95,
                    "styling_note": "Perfect match for your style"
                }
            ],
            "metadata": {
                "source": "mock",
                "session_id": "session_456"
            }
        })
        
        response = client.post("/api/retailer/recommendations", json={
            "product_id": "PROD_001",
            "user_id": "user_123",
            "interaction_type": "click",
            "session_id": "session_456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["recommendations"]) > 0
        assert data["recommendations"][0]["product_id"] == "REC_001"
    
    def test_get_batch_recommendations(self, mock_retailer_service):
        """Test batch recommendation endpoint"""
        mock_retailer_service.get_retailer_recommendations = AsyncMock(side_effect=[
            {
                "status": "success",
                "recommendations": [
                    {"product_id": "REC_001", "score": 0.9},
                    {"product_id": "REC_002", "score": 0.8}
                ]
            },
            {
                "status": "success",
                "recommendations": [
                    {"product_id": "REC_002", "score": 0.85},
                    {"product_id": "REC_003", "score": 0.75}
                ]
            }
        ])
        
        mock_retailer_service.create_outfit_from_interactions = AsyncMock(return_value={
            "outfit_id": "outfit_123",
            "items": [
                {"product_id": "PROD_001", "name": "Item 1", "price": 50},
                {"product_id": "PROD_002", "name": "Item 2", "price": 75}
            ],
            "total_price": 125,
            "compatibility_score": 0.85
        })
        
        response = client.post("/api/retailer/recommendations/batch", json={
            "interactions": [
                {
                    "product_id": "PROD_001",
                    "interaction_type": "click"
                },
                {
                    "product_id": "PROD_002",
                    "interaction_type": "like"
                }
            ],
            "create_outfit": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["interaction_count"] == 2
        assert "suggested_outfit" in data
        assert data["suggested_outfit"]["outfit_id"] == "outfit_123"
    
    def test_get_interaction_history(self, mock_retailer_service):
        """Test interaction history endpoint"""
        mock_retailer_service.get_interaction_history = AsyncMock(return_value=[
            {
                "product_id": "PROD_001",
                "user_id": "user_123",
                "type": "click",
                "timestamp": "2024-01-01T12:00:00",
                "session_id": "session_456"
            },
            {
                "product_id": "PROD_002",
                "user_id": "user_123",
                "type": "like",
                "timestamp": "2024-01-01T12:05:00",
                "session_id": "session_456"
            }
        ])
        
        response = client.get("/api/retailer/interactions/history?session_id=session_456")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["interactions"]) == 2
        assert data["interactions"][0]["product_id"] == "PROD_001"
    
    def test_get_interaction_history_no_params(self):
        """Test interaction history endpoint without required parameters"""
        response = client.get("/api/retailer/interactions/history")
        
        assert response.status_code == 400
        assert "session_id or user_id must be provided" in response.json()["detail"]
    
    def test_create_outfit_from_interactions(self, mock_retailer_service):
        """Test outfit creation from interactions"""
        mock_retailer_service.create_outfit_from_interactions = AsyncMock(return_value={
            "outfit_id": "outfit_789",
            "items": [
                {"product_id": "PROD_001", "name": "Top", "price": 45},
                {"product_id": "PROD_002", "name": "Bottom", "price": 65},
                {"product_id": "PROD_003", "name": "Shoes", "price": 85}
            ],
            "total_price": 195,
            "created_from": "user_interactions",
            "compatibility_score": 0.88
        })
        
        response = client.post("/api/retailer/outfit/from-interactions", json={
            "product_ids": ["PROD_001", "PROD_002", "PROD_003"],
            "user_id": "user_123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["outfit"]["outfit_id"] == "outfit_789"
        assert len(data["outfit"]["items"]) == 3
        assert data["outfit"]["total_price"] == 195
    
    def test_create_outfit_empty_products(self):
        """Test outfit creation with empty product list"""
        response = client.post("/api/retailer/outfit/from-interactions", json={
            "product_ids": []
        })
        
        assert response.status_code == 400
        assert "At least one product_id must be provided" in response.json()["detail"]
    
    def test_submit_recommendation_feedback(self):
        """Test feedback submission endpoint"""
        response = client.post("/api/retailer/feedback", json={
            "product_id": "REC_001",
            "feedback_type": "helpful",
            "user_id": "user_123",
            "session_id": "session_456",
            "notes": "This recommendation was very relevant"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "feedback_id" in data
    
    def test_recommendations_with_context(self, mock_retailer_service):
        """Test recommendations with detailed context"""
        mock_retailer_service.get_retailer_recommendations = AsyncMock(return_value={
            "status": "success",
            "recommendations": [
                {
                    "product_id": "REC_001",
                    "name": "Contextual Recommendation",
                    "score": 0.92,
                    "category": "tops",
                    "outfit_potential": 0.85
                }
            ]
        })
        
        response = client.post("/api/retailer/recommendations", json={
            "product_id": "PROD_001",
            "interaction_type": "like",
            "context": {
                "categories": ["tops", "dresses"],
                "price_range": {"min": 30, "max": 150},
                "occasion": "casual",
                "style_preference": "modern"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify context was passed to service
        mock_retailer_service.get_retailer_recommendations.assert_called_with(
            product_id="PROD_001",
            user_id=None,
            interaction_type="like",
            session_id=None,
            context={
                "categories": ["tops", "dresses"],
                "price_range": {"min": 30, "max": 150},
                "occasion": "casual",
                "style_preference": "modern"
            }
        )
    
    def test_error_handling_in_recommendations(self, mock_retailer_service):
        """Test error handling in recommendation endpoint"""
        mock_retailer_service.get_retailer_recommendations = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        
        response = client.post("/api/retailer/recommendations", json={
            "product_id": "PROD_ERROR"
        })
        
        assert response.status_code == 500
        assert "Service unavailable" in response.json()["detail"]