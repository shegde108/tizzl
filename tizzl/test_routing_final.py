#!/usr/bin/env python3
"""Test script to verify all queries now properly return product recommendations"""

from services.query_router import QueryRouter, QueryType

def test_final_routing():
    """Test that various query types are handled correctly"""
    
    test_cases = [
        # Original problematic queries
        ("do you have outfit suggestions", QueryType.RECOMMENDATION, True),
        ("i want to style my blue jeans with a formal or informal top", QueryType.RECOMMENDATION, True),
        ("outfits for summer party brunch", QueryType.RECOMMENDATION, True),
        ("do you have light sweaters?", QueryType.RECOMMENDATION, True),
        
        # General styling advice that should now return products
        ("How do I match colors?", QueryType.RECOMMENDATION, True),
        ("What colors go well together?", QueryType.RECOMMENDATION, True),
        ("Give me some fashion tips", QueryType.RECOMMENDATION, True),
        
        # Direct product requests
        ("Show me summer dresses", QueryType.RECOMMENDATION, True),
        ("Find me a formal suit", QueryType.RECOMMENDATION, True),
        
        # Only greetings, help, and feedback should skip processing
        ("Hello", QueryType.GREETING, False),
        ("What can you do?", QueryType.HELP, False),
        ("This isn't working properly", QueryType.FEEDBACK, False),
    ]
    
    print("Query Routing Test Results:")
    print("=" * 70)
    
    all_passed = True
    for query, expected_type, should_process in test_cases:
        result = QueryRouter.route_query(query)
        actual_type = QueryType[result['type'].upper()]
        skip_processing = result['skip_processing']
        actual_processes = not skip_processing
        
        passed = (actual_type == expected_type and actual_processes == should_process)
        status = "✓" if passed else "✗"
        
        print(f"{status} Query: '{query[:40]}...' if len(query) > 40 else '{query}'")
        print(f"  Expected: {expected_type.value}, Process={should_process}")
        print(f"  Actual: {result['type']}, Process={actual_processes}")
        
        if not passed:
            all_passed = False
            print(f"  FAILED: Type mismatch or processing mismatch")
        print()
    
    if all_passed:
        print("✅ All tests passed! All fashion-related queries now return product recommendations.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    return all_passed

if __name__ == "__main__":
    success = test_final_routing()
    exit(0 if success else 1)