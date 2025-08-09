#!/usr/bin/env python3
"""
Performance testing script to compare original vs optimized endpoints
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, Any, List

# API Base URL
BASE_URL = "http://localhost:8000"

# Test queries
TEST_QUERIES = [
    # Greetings (should be instant with optimized version)
    {"query": "Hi", "type": "greeting"},
    {"query": "Hello there!", "type": "greeting"},
    
    # Help queries (should be instant with optimized version)
    {"query": "How do you work?", "type": "help"},
    {"query": "What can you help me with?", "type": "help"},
    
    # Styling queries (should be faster with optimized version)
    {"query": "What should I wear to a job interview?", "type": "styling"},
    {"query": "Show me casual summer outfits", "type": "styling"},
    {"query": "I need a dress for a wedding", "type": "styling"},
    {"query": "What goes well with black jeans?", "type": "styling"},
]

async def test_endpoint(session: aiohttp.ClientSession, endpoint: str, query: str) -> Dict[str, Any]:
    """Test a single endpoint and measure response time"""
    start_time = time.time()
    
    try:
        payload = {
            "query": query,
            "max_results": 10
        }
        
        async with session.post(f"{BASE_URL}{endpoint}", json=payload) as response:
            result = await response.json()
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "success": True,
                "time_ms": elapsed_time,
                "processing_time_ms": result.get("processing_time_ms", 0),
                "has_recommendations": len(result.get("recommendations", [])) > 0,
                "response_length": len(json.dumps(result))
            }
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        return {
            "success": False,
            "time_ms": elapsed_time,
            "error": str(e)
        }

async def test_advice_endpoint(session: aiohttp.ClientSession, endpoint: str, query: str) -> Dict[str, Any]:
    """Test advice endpoint"""
    start_time = time.time()
    
    try:
        params = {"query": query}
        
        async with session.post(f"{BASE_URL}{endpoint}", params=params) as response:
            result = await response.json()
            elapsed_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "time_ms": elapsed_time,
                "response_length": len(result.get("advice", ""))
            }
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        return {
            "success": False,
            "time_ms": elapsed_time,
            "error": str(e)
        }

async def run_performance_tests():
    """Run performance comparison tests"""
    print("=" * 60)
    print("PERFORMANCE COMPARISON: Original vs Optimized Endpoints")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test recommendation endpoints
        print("\n📊 RECOMMENDATION ENDPOINT TESTS")
        print("-" * 60)
        
        for test_case in TEST_QUERIES:
            query = test_case["query"]
            query_type = test_case["type"]
            
            print(f"\n🔍 Query: '{query}' (Type: {query_type})")
            
            # Test original endpoint
            print("  Original endpoint (/api/stylist/recommend):")
            original_result = await test_endpoint(session, "/api/stylist/recommend", query)
            if original_result["success"]:
                print(f"    ✅ Response time: {original_result['time_ms']:.1f}ms")
                print(f"    📝 Processing time: {original_result['processing_time_ms']}ms")
                print(f"    📦 Response size: {original_result['response_length']} bytes")
            else:
                print(f"    ❌ Error: {original_result.get('error', 'Unknown error')}")
            
            # Test optimized endpoint
            print("  Optimized endpoint (/api/v2/stylist/recommend):")
            optimized_result = await test_endpoint(session, "/api/v2/stylist/recommend", query)
            if optimized_result["success"]:
                print(f"    ✅ Response time: {optimized_result['time_ms']:.1f}ms")
                print(f"    📝 Processing time: {optimized_result['processing_time_ms']}ms")
                print(f"    📦 Response size: {optimized_result['response_length']} bytes")
            else:
                print(f"    ❌ Error: {optimized_result.get('error', 'Unknown error')}")
            
            # Calculate improvement
            if original_result["success"] and optimized_result["success"]:
                improvement = ((original_result['time_ms'] - optimized_result['time_ms']) / 
                              original_result['time_ms'] * 100)
                print(f"    🚀 Improvement: {improvement:.1f}% faster")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Test advice endpoints for greetings
        print("\n\n📊 ADVICE ENDPOINT TESTS (Greetings)")
        print("-" * 60)
        
        greeting_queries = ["Hello", "Hi there", "Hey!"]
        
        for query in greeting_queries:
            print(f"\n🔍 Query: '{query}'")
            
            # Test original advice endpoint
            print("  Original endpoint (/api/v2/stylist/advice):")
            original_result = await test_advice_endpoint(session, "/api/v2/stylist/advice", query)
            if original_result["success"]:
                print(f"    ✅ Response time: {original_result['time_ms']:.1f}ms")
                print(f"    📦 Response length: {original_result['response_length']} chars")
            else:
                print(f"    ❌ Error: {original_result.get('error', 'Unknown error')}")
            
            # Test optimized advice endpoint
            print("  Optimized endpoint (/api/v2/stylist/advice):")
            optimized_result = await test_advice_endpoint(session, "/api/v2/stylist/advice", query)
            if optimized_result["success"]:
                print(f"    ✅ Response time: {optimized_result['time_ms']:.1f}ms")
                print(f"    📦 Response length: {optimized_result['response_length']} chars")
            else:
                print(f"    ❌ Error: {optimized_result.get('error', 'Unknown error')}")
            
            # Calculate improvement
            if original_result["success"] and optimized_result["success"]:
                improvement = ((original_result['time_ms'] - optimized_result['time_ms']) / 
                              original_result['time_ms'] * 100)
                print(f"    🚀 Improvement: {improvement:.1f}% faster")
            
            await asyncio.sleep(0.5)
        
        # Test caching behavior
        print("\n\n📊 CACHE PERFORMANCE TEST")
        print("-" * 60)
        
        cache_query = "What should I wear to a business meeting?"
        print(f"Testing query: '{cache_query}'")
        
        # First request (cache miss)
        print("\n  First request (cache miss):")
        first_result = await test_endpoint(session, "/api/v2/stylist/recommend", cache_query)
        if first_result["success"]:
            print(f"    ✅ Response time: {first_result['time_ms']:.1f}ms")
        
        # Second request (cache hit)
        print("  Second request (cache hit):")
        second_result = await test_endpoint(session, "/api/v2/stylist/recommend", cache_query)
        if second_result["success"]:
            print(f"    ✅ Response time: {second_result['time_ms']:.1f}ms")
        
        if first_result["success"] and second_result["success"]:
            cache_improvement = ((first_result['time_ms'] - second_result['time_ms']) / 
                                first_result['time_ms'] * 100)
            print(f"    🚀 Cache improvement: {cache_improvement:.1f}% faster")

def main():
    """Main entry point"""
    print("\n🚀 Starting Performance Tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        asyncio.run(run_performance_tests())
        print("\n\n✅ Performance tests completed!")
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")

if __name__ == "__main__":
    main()