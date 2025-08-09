import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.query_router import QueryRouter, QueryType
from services.unified_llm_service import UnifiedLLMService
from services.optimized_stylist_service import OptimizedStylistService
from models import UserQuery, Product, Category, ProductAttribute

class TestQueryRouter:
    """Test cases for the query router"""
    
    def test_greeting_detection(self):
        """Test that greetings are properly detected"""
        greetings = [
            "Hi",
            "Hello",
            "Hey there",
            "Good morning",
            "Howdy",
            "Hello!",
            "hi",
            "HEY"
        ]
        
        for greeting in greetings:
            query_type, confidence = QueryRouter.classify_query(greeting)
            assert query_type == QueryType.GREETING, f"Failed to detect greeting: {greeting}"
            assert confidence > 0.9
    
    def test_styling_query_detection(self):
        """Test that styling queries are properly detected"""
        styling_queries = [
            "What should I wear to a wedding?",
            "I need an outfit for work",
            "Show me summer dresses",
            "What goes with black jeans?",
            "Find me a formal suit",
            "I want casual clothes for the weekend"
        ]
        
        for query in styling_queries:
            query_type, confidence = QueryRouter.classify_query(query)
            assert query_type == QueryType.STYLING, f"Failed to detect styling query: {query}"
            assert confidence > 0.5
    
    def test_help_query_detection(self):
        """Test that help queries are properly detected"""
        help_queries = [
            "How do you work?",
            "What can you help me with?",
            "Can you assist me?",
            "I need help",
            "What are your features?"
        ]
        
        for query in help_queries:
            query_type, confidence = QueryRouter.classify_query(query)
            assert query_type == QueryType.HELP, f"Failed to detect help query: {query}"
    
    def test_feedback_query_detection(self):
        """Test that feedback queries are properly detected"""
        feedback_queries = [
            "I want to report a bug",
            "This isn't working properly",
            "I have feedback",
            "There's a problem with the recommendations"
        ]
        
        for query in feedback_queries:
            query_type, confidence = QueryRouter.classify_query(query)
            assert query_type == QueryType.FEEDBACK, f"Failed to detect feedback query: {query}"
    
    def test_should_skip_expensive_processing(self):
        """Test that certain query types skip expensive processing"""
        assert QueryRouter.should_skip_expensive_processing(QueryType.GREETING)
        assert QueryRouter.should_skip_expensive_processing(QueryType.HELP)
        assert QueryRouter.should_skip_expensive_processing(QueryType.FEEDBACK)
        assert not QueryRouter.should_skip_expensive_processing(QueryType.STYLING)
        assert not QueryRouter.should_skip_expensive_processing(QueryType.GENERAL_QUESTION)
    
    def test_routing_result_structure(self):
        """Test that routing results have the correct structure"""
        result = QueryRouter.route_query("Hello")
        
        assert 'type' in result
        assert 'confidence' in result
        assert 'skip_processing' in result
        assert 'response' in result
        
        assert result['type'] == 'greeting'
        assert result['skip_processing'] is True
        assert result['response'] is not None

@pytest.mark.asyncio
class TestUnifiedLLMService:
    """Test cases for the unified LLM service"""
    
    async def test_process_styling_query_structure(self):
        """Test that the unified LLM service returns the correct structure"""
        service = UnifiedLLMService()
        
        # Mock products
        products = [
            Product(
                product_id="TEST001",
                name="Test Shirt",
                category=Category.TOPS,
                description="A test shirt",
                attributes=ProductAttribute(),
                price=49.99
            ),
            Product(
                product_id="TEST002",
                name="Test Pants",
                category=Category.BOTTOMS,
                description="Test pants",
                attributes=ProductAttribute(),
                price=79.99
            )
        ]
        
        # Mock the LLM response
        with patch.object(service, '_generate_structured_response', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = service._generate_mock_structured()
            
            result = await service.process_styling_query(
                "What should I wear?",
                products
            )
            
            # Check structure
            assert 'search_terms' in result
            assert 'ranked_products' in result
            assert 'outfits' in result
            assert 'styling_advice' in result
            
            # Check types
            assert isinstance(result['search_terms'], list)
            assert isinstance(result['ranked_products'], list)
            assert isinstance(result['outfits'], list)
            assert isinstance(result['styling_advice'], str)
    
    async def test_fallback_response(self):
        """Test that fallback response works when LLM fails"""
        service = UnifiedLLMService()
        
        products = [
            Product(
                product_id="TEST001",
                name="Test Item",
                category=Category.TOPS,
                description="Test",
                attributes=ProductAttribute(),
                price=50.00
            )
        ]
        
        result = service._get_fallback_unified_response("test query", products)
        
        assert result is not None
        assert 'search_terms' in result
        assert 'ranked_products' in result
        assert len(result['ranked_products']) > 0

@pytest.mark.asyncio
class TestOptimizedStylistService:
    """Test cases for the optimized stylist service"""
    
    async def test_greeting_handling(self):
        """Test that greetings are handled without expensive processing"""
        service = OptimizedStylistService()
        
        query = UserQuery(
            query="Hello",
            user_id="test_user"
        )
        
        with patch.object(service.retrieval_service, 'retrieve_products', new_callable=AsyncMock) as mock_retrieve:
            response = await service.process_query(query)
            
            # Should not call retrieve_products for greetings
            mock_retrieve.assert_not_called()
            
            # Should return quickly with greeting response
            assert response.processing_time_ms < 100
            assert "Hello" in response.styling_advice or "Hi" in response.styling_advice
            assert len(response.recommendations) == 0
    
    async def test_styling_query_processing(self):
        """Test that styling queries are processed correctly"""
        service = OptimizedStylistService()
        
        query = UserQuery(
            query="What should I wear to a wedding?",
            user_id="test_user",
            budget=500
        )
        
        # Mock products
        mock_products = [
            Product(
                product_id="DRESS001",
                name="Elegant Dress",
                category=Category.DRESSES,
                description="Perfect for weddings",
                attributes=ProductAttribute(),
                price=199.99
            )
        ]
        
        with patch.object(service, '_optimized_product_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_products
            
            with patch.object(service.unified_llm, 'process_styling_query', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = {
                    'search_terms': ['wedding', 'formal', 'dress'],
                    'ranked_products': [
                        {'product': mock_products[0], 'score': 0.95, 'reason': 'Perfect match'}
                    ],
                    'outfits': [{
                        'name': 'Wedding Guest',
                        'description': 'Elegant outfit',
                        'products': mock_products,
                        'styling_tips': ['Add jewelry'],
                        'total_price': 199.99
                    }],
                    'styling_advice': 'Great choice for a wedding'
                }
                
                response = await service.process_query(query)
                
                # Check that styling query was processed
                assert len(response.recommendations) > 0
                assert response.styling_advice != ""
                mock_search.assert_called_once()
                mock_llm.assert_called_once()
    
    async def test_cache_integration(self):
        """Test that caching works correctly"""
        service = OptimizedStylistService()
        
        query = UserQuery(
            query="Summer outfit ideas",
            user_id="test_user"
        )
        
        # Mock cache hit
        with patch.object(service.cache_service, 'get_query_result', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'response_id': 'cached_id',
                'user_query': query.query,
                'recommendations': [],
                'styling_advice': 'Cached response',
                'processing_time_ms': 10
            }
            
            response = await service.process_query(query)
            
            # Should return cached response
            assert response.styling_advice == 'Cached response'
            assert response.processing_time_ms < 50  # Should be very fast
    
    async def test_optimized_filters(self):
        """Test that filters are built correctly"""
        service = OptimizedStylistService()
        
        query = UserQuery(
            query="Test",
            budget=200,
            preferred_categories=["tops", "bottoms"],
            include_sale_items=False
        )
        
        filters = service._build_optimized_filters(query, None)
        
        assert filters['in_stock'] is True
        assert filters['max_price'] == 200
        assert filters['category'] == ["tops", "bottoms"]
        assert filters['on_sale'] is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])