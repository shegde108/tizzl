import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from tizzl.services.retailer_integration import RetailerRecommendationService

class TestRetailerRecommendationService:
    """Test suite for RetailerRecommendationService"""
    
    @pytest.fixture
    async def service(self):
        """Create a test service instance"""
        service = RetailerRecommendationService()
        yield service
        await service.close()
    
    @pytest.fixture
    async def service_with_api(self):
        """Create a service instance with mock API configuration"""
        service = RetailerRecommendationService(
            retailer_api_url="https://api.retailer.com",
            api_key="test_api_key"
        )
        yield service
        await service.close()
    
    @pytest.mark.asyncio
    async def test_get_retailer_recommendations_click(self, service):
        """Test getting recommendations for a click interaction"""
        result = await service.get_retailer_recommendations(
            product_id="TEST_001",
            user_id="user_123",
            interaction_type="click",
            session_id="session_456"
        )
        
        assert result["status"] == "success"
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert result["metadata"]["source"] == "mock"
        
        # Check first recommendation
        first_rec = result["recommendations"][0]
        assert "product_id" in first_rec
        assert "styling_note" in first_rec
        assert "outfit_potential" in first_rec
    
    @pytest.mark.asyncio
    async def test_get_retailer_recommendations_like(self, service):
        """Test getting recommendations for a like interaction"""
        result = await service.get_retailer_recommendations(
            product_id="TEST_002",
            interaction_type="like",
            context={"categories": ["tops"], "price_range": {"min": 20, "max": 100}}
        )
        
        assert result["status"] == "success"
        recommendations = result["recommendations"]
        
        # Check styling notes for liked items
        for rec in recommendations:
            assert "styling_note" in rec
            assert "beautifully" in rec["styling_note"] or "loved" in rec["styling_note"]
    
    @pytest.mark.asyncio
    async def test_get_retailer_recommendations_with_context(self, service):
        """Test recommendations with additional context"""
        context = {
            "categories": ["dresses", "tops"],
            "price_range": {"min": 50, "max": 200},
            "occasion": "casual",
            "style_preference": "modern",
            "limit": 10
        }
        
        result = await service.get_retailer_recommendations(
            product_id="TEST_003",
            interaction_type="view_details",
            context=context
        )
        
        assert result["status"] == "success"
        assert len(result["recommendations"]) <= 10
        
        # Check outfit potential calculation
        for rec in result["recommendations"]:
            assert 0 <= rec["outfit_potential"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_interaction_recording(self, service):
        """Test that interactions are properly recorded"""
        # Record an interaction
        await service.get_retailer_recommendations(
            product_id="TEST_004",
            user_id="user_789",
            interaction_type="add_to_cart",
            session_id="session_789"
        )
        
        # Check interaction history
        history = await service.get_interaction_history(session_id="session_789")
        
        assert len(history) > 0
        assert history[0]["product_id"] == "TEST_004"
        assert history[0]["type"] == "add_to_cart"
        assert history[0]["session_id"] == "session_789"
    
    @pytest.mark.asyncio
    async def test_create_outfit_from_interactions(self, service):
        """Test creating an outfit from multiple interactions"""
        product_ids = ["PROD_001", "PROD_002", "PROD_003"]
        
        outfit = await service.create_outfit_from_interactions(
            product_ids=product_ids,
            user_id="user_123"
        )
        
        assert "outfit_id" in outfit
        assert len(outfit["items"]) == 3
        assert outfit["total_price"] > 0
        assert outfit["created_from"] == "user_interactions"
        assert 0 <= outfit["compatibility_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_external_api_call(self, service_with_api):
        """Test external API integration (mocked)"""
        with patch.object(service_with_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "recommendations": [
                    {"product_id": "REC_001", "name": "External Rec 1", "score": 0.9},
                    {"product_id": "REC_002", "name": "External Rec 2", "score": 0.8}
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = await service_with_api.get_retailer_recommendations(
                product_id="TEST_005",
                user_id="user_123"
            )
            
            assert result["status"] == "success"
            assert result["metadata"]["source"] == "retailer_api"
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test error handling in recommendations"""
        with patch.object(service, '_generate_mock_recommendations', side_effect=Exception("Test error")):
            result = await service.get_retailer_recommendations(
                product_id="ERROR_001"
            )
            
            assert result["status"] == "error"
            assert "Test error" in result["error"]
            assert result["recommendations"] == []
    
    @pytest.mark.asyncio
    async def test_outfit_potential_calculation(self, service):
        """Test outfit potential score calculation"""
        # Test complementary item
        rec_complementary = {"type": "complementary"}
        score = service._calculate_outfit_potential(rec_complementary, None)
        assert score >= 0.8
        
        # Test frequently bought item
        rec_frequent = {"type": "frequently_bought"}
        score = service._calculate_outfit_potential(rec_frequent, None)
        assert score >= 0.7
        
        # Test with matching context
        rec_match = {"type": "similar_style", "occasion": "casual", "style": "modern"}
        context = {"occasion": "casual", "style_preference": "modern"}
        score = service._calculate_outfit_potential(rec_match, context)
        assert score >= 0.7
    
    @pytest.mark.asyncio
    async def test_interaction_history_filtering(self, service):
        """Test filtering interaction history by user"""
        # Record multiple interactions
        await service.get_retailer_recommendations(
            product_id="TEST_006",
            user_id="user_A",
            interaction_type="click",
            session_id="session_A"
        )
        
        await service.get_retailer_recommendations(
            product_id="TEST_007",
            user_id="user_B",
            interaction_type="like",
            session_id="session_B"
        )
        
        # Get history for specific user
        history_a = await service.get_interaction_history(
            session_id="session_A",
            user_id="user_A"
        )
        
        for interaction in history_a:
            assert interaction["user_id"] == "user_A" or interaction["session_id"] == "session_A"