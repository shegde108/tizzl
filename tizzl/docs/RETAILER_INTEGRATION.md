# Retailer Recommendation Integration

## Overview

The Retailer Integration module enables Tizzl to leverage a retailer's existing recommendation system when users interact with products in the AI stylist chat. This creates a seamless bridge between AI-powered styling advice and the retailer's own recommendation engine.

## Key Features

### 1. Product Interaction Tracking
- **Click Tracking**: Records when users click on products in the chat
- **Like/Favorite**: Tracks products users explicitly like
- **Add to Cart**: Monitors cart additions from recommendations
- **View Details**: Captures detailed product views

### 2. Hybrid Recommendations
Combines retailer's recommendations with AI styling context:
- Retailer's algorithm provides base recommendations
- AI enhances with styling notes and outfit potential
- Smart ranking based on interaction type and context

### 3. Outfit Creation
Automatically generates outfit suggestions from user interactions:
- Groups liked/clicked items into cohesive outfits
- Calculates compatibility scores
- Provides total pricing and styling tips

## API Endpoints

### Get Recommendations
```http
POST /api/retailer/recommendations
```

**Request Body:**
```json
{
  "product_id": "PROD_001",
  "user_id": "user_123",
  "interaction_type": "click",
  "session_id": "session_456",
  "context": {
    "categories": ["tops", "dresses"],
    "price_range": {"min": 30, "max": 150},
    "occasion": "casual"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "interaction": {
    "product_id": "PROD_001",
    "type": "click",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "recommendations": [
    {
      "product_id": "REC_001",
      "name": "Similar Style Top",
      "reason": "Based on your click of similar items",
      "score": 0.95,
      "styling_note": "Customers who viewed this also loved this piece",
      "outfit_potential": 0.85
    }
  ],
  "metadata": {
    "source": "retailer_api",
    "session_id": "session_456"
  }
}
```

### Batch Recommendations
```http
POST /api/retailer/recommendations/batch
```

Process multiple interactions and get aggregated recommendations.

**Request Body:**
```json
{
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
  "create_outfit": true
}
```

### Interaction History
```http
GET /api/retailer/interactions/history?session_id=session_456
```

Retrieve interaction history for analysis and personalization.

### Create Outfit from Interactions
```http
POST /api/retailer/outfit/from-interactions
```

Generate outfit suggestions from products the user has interacted with.

**Request Body:**
```json
{
  "product_ids": ["PROD_001", "PROD_002", "PROD_003"],
  "user_id": "user_123"
}
```

### Submit Feedback
```http
POST /api/retailer/feedback
```

Track feedback on recommendations for continuous improvement.

## Integration Guide

### 1. Configure Retailer API

Add to `.env`:
```env
RETAILER_API_URL=https://api.yourretailer.com
RETAILER_API_KEY=your_api_key_here
```

### 2. Implement Custom Adapter

If your retailer's API has a different format, create a custom adapter:

```python
# tizzl/services/custom_retailer_adapter.py
from tizzl.services.retailer_integration import RetailerRecommendationService

class CustomRetailerAdapter(RetailerRecommendationService):
    async def _fetch_external_recommendations(self, product_id, user_id, context):
        # Transform request to match your API format
        custom_params = self._transform_params(product_id, user_id, context)
        
        # Call your API
        response = await self.client.post(
            f"{self.retailer_api_url}/your-endpoint",
            json=custom_params
        )
        
        # Transform response to standard format
        return self._transform_response(response.json())
```

### 3. Frontend Integration

```javascript
// Track product click in chat
async function onProductClick(productId) {
    const response = await fetch('/api/retailer/recommendations', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            product_id: productId,
            interaction_type: 'click',
            session_id: currentSessionId,
            context: {
                categories: activeFilters.categories,
                price_range: activeFilters.priceRange
            }
        })
    });
    
    const data = await response.json();
    displayRecommendations(data.recommendations);
}

// Track product like
async function onProductLike(productId) {
    await trackInteraction(productId, 'like');
    updateLikedProducts(productId);
}
```

## Testing

### Run All Tests
```bash
cd tizzl
pytest tests/test_retailer_integration.py tests/test_retailer_endpoints.py -v
```

### Test Coverage
```bash
pytest tests/test_retailer_*.py --cov=tizzl.services.retailer_integration --cov-report=html
```

### Integration Testing
```python
# tests/test_retailer_integration_live.py
import pytest
from tizzl.services.retailer_integration import RetailerRecommendationService

@pytest.mark.integration
async def test_live_retailer_api():
    service = RetailerRecommendationService(
        retailer_api_url="https://staging-api.retailer.com",
        api_key="test_key"
    )
    
    result = await service.get_retailer_recommendations(
        product_id="LIVE_PROD_001",
        interaction_type="click"
    )
    
    assert result["status"] == "success"
    assert len(result["recommendations"]) > 0
```

## Performance Considerations

### Caching
- Interaction data is cached in memory for session continuity
- Consider Redis for production deployments
- Cache TTL: 15 minutes for recommendations

### Rate Limiting
- Default: 100 requests per minute per user
- Batch endpoints for multiple interactions
- Async processing for non-blocking operations

### Optimization Tips
1. Use batch endpoints when processing multiple interactions
2. Implement webhook callbacks for async processing
3. Cache frequently accessed recommendations
4. Use CDN for product images in recommendations

## Analytics Integration

Track key metrics:
- Click-through rate (CTR) on recommendations
- Conversion rate from recommendations
- Outfit completion rate
- User engagement by interaction type

```python
# Example analytics tracking
async def track_recommendation_event(event_type, product_id, user_id):
    analytics_data = {
        "event": event_type,
        "product_id": product_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "ai_stylist_chat"
    }
    
    # Send to analytics service
    await analytics_service.track(analytics_data)
```

## Troubleshooting

### Common Issues

1. **No recommendations returned**
   - Check API credentials in `.env`
   - Verify product_id exists in retailer's system
   - Check network connectivity to retailer API

2. **Slow response times**
   - Implement caching for frequent queries
   - Use batch endpoints for multiple products
   - Check retailer API response times

3. **Incorrect styling context**
   - Verify context parameters are properly formatted
   - Check outfit_potential calculation logic
   - Review interaction type mapping

## Security Considerations

1. **API Key Management**
   - Store keys in environment variables
   - Rotate keys regularly
   - Use separate keys for staging/production

2. **Data Privacy**
   - Anonymize user data when possible
   - Implement GDPR compliance for EU users
   - Clear session data after expiration

3. **Rate Limiting**
   - Implement per-user rate limits
   - Use exponential backoff for retries
   - Monitor for abuse patterns

## Future Enhancements

- [ ] Machine learning model for outfit compatibility scoring
- [ ] Real-time collaborative filtering
- [ ] Visual similarity search integration
- [ ] A/B testing framework for recommendations
- [ ] Personalization based on purchase history
- [ ] Social sharing of outfit combinations