import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QueryType(Enum):
    GREETING = "greeting"
    STYLING = "styling"
    GENERAL_QUESTION = "general_question"
    FEEDBACK = "feedback"
    HELP = "help"
    UNKNOWN = "unknown"

class QueryRouter:
    """Routes queries to appropriate handlers based on intent detection"""
    
    # Greeting patterns
    GREETING_PATTERNS = [
        r'^(hi|hey|hello|howdy|greetings?|good\s+(morning|afternoon|evening|day))(\s+there)?[!.?]*$',
        r'^(yo|sup|wassup|what\'?s\s+up)[!.?]*$',
        r'^(bonjour|hola|ciao|namaste|salut)[!.?]*$',
    ]
    
    # Help/feedback patterns
    HELP_PATTERNS = [
        r'\b(help|assist|support|guide|how\s+to\s+use|tutorial|instructions?)\b',
        r'\b(what\s+can\s+you\s+do|how\s+do\s+you\s+work|capabilities|features?)\b',
    ]
    
    FEEDBACK_PATTERNS = [
        r'\b(feedback|complaint|suggestion|report|issue|bug|problem\s+with)\b',
        r'\b(not\s+working|broken|error|wrong|incorrect)\b',
    ]
    
    # Fashion/styling keywords that indicate styling intent
    STYLING_KEYWORDS = [
        'outfit', 'wear', 'style', 'fashion', 'clothes', 'clothing', 
        'dress', 'shirt', 'pants', 'jeans', 'skirt', 'top', 'bottom',
        'shoes', 'accessories', 'bag', 'jewelry', 'match', 'coordinate',
        'occasion', 'event', 'date', 'work', 'casual', 'formal',
        'color', 'pattern', 'trend', 'season', 'summer', 'winter',
        'look', 'appearance', 'wardrobe', 'closet', 'shopping'
    ]
    
    # General question indicators
    GENERAL_QUESTION_PATTERNS = [
        r'^(what|who|when|where|why|how|which|whose|whom)\s+',
        r'\b(explain|tell\s+me|describe|clarify)\b',
    ]
    
    @classmethod
    def classify_query(cls, query: str) -> Tuple[QueryType, float]:
        """
        Classify a query and return the type with confidence score
        
        Returns:
            Tuple of (QueryType, confidence_score)
        """
        query_lower = query.lower().strip()
        
        # Check for greetings first (highest priority for user experience)
        if cls._is_greeting(query_lower):
            return QueryType.GREETING, 0.95
        
        # Check for help requests
        if cls._is_help_request(query_lower):
            return QueryType.HELP, 0.9
        
        # Check for feedback/complaints
        if cls._is_feedback(query_lower):
            return QueryType.FEEDBACK, 0.9
        
        # Check for styling/fashion queries
        styling_score = cls._calculate_styling_score(query_lower)
        if styling_score > 0.3:  # Threshold for styling queries
            return QueryType.STYLING, min(styling_score, 0.95)
        
        # Check if it's a general question
        if cls._is_general_question(query_lower):
            # Could still be styling-related, check keywords
            if styling_score > 0.1:
                return QueryType.STYLING, 0.6
            return QueryType.GENERAL_QUESTION, 0.7
        
        # Default to styling if uncertain (maintains backward compatibility)
        if len(query_lower.split()) > 3:  # Longer queries likely styling
            return QueryType.STYLING, 0.5
        
        return QueryType.UNKNOWN, 0.3
    
    @classmethod
    def _is_greeting(cls, query: str) -> bool:
        """Check if query is a greeting"""
        for pattern in cls.GREETING_PATTERNS:
            if re.match(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _is_help_request(cls, query: str) -> bool:
        """Check if query is asking for help"""
        for pattern in cls.HELP_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _is_feedback(cls, query: str) -> bool:
        """Check if query is providing feedback or reporting issues"""
        for pattern in cls.FEEDBACK_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _is_general_question(cls, query: str) -> bool:
        """Check if query is a general question"""
        for pattern in cls.GENERAL_QUESTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return query.endswith('?')
    
    @classmethod
    def _calculate_styling_score(cls, query: str) -> float:
        """Calculate how likely a query is about styling/fashion"""
        words = query.lower().split()
        if not words:
            return 0.0
        
        keyword_count = sum(1 for word in words if word in cls.STYLING_KEYWORDS)
        score = keyword_count / len(words)
        
        # Boost score for certain strong indicators
        if any(phrase in query for phrase in ['what should i wear', 'outfit for', 'style for', 'dress for']):
            score += 0.5
        
        return min(score, 1.0)
    
    @classmethod
    def get_greeting_response(cls) -> str:
        """Get an appropriate greeting response"""
        import random
        responses = [
            "Hello! I'm your AI fashion stylist. How can I help you find the perfect outfit today?",
            "Hi there! Ready to discover some amazing style recommendations? Tell me what you're looking for!",
            "Welcome! I'm here to help you look and feel your best. What occasion are you dressing for?",
            "Hey! Let's find you something fabulous to wear. What's on your style agenda today?",
            "Hello! Whether you need a complete outfit or style advice, I'm here to help. What can I do for you?"
        ]
        return random.choice(responses)
    
    @classmethod
    def get_help_response(cls) -> str:
        """Get help/guidance response"""
        return """I'm your AI Fashion Stylist! Here's how I can help:

🎯 **What I Can Do:**
• Create complete outfit recommendations based on your needs
• Suggest items that match your existing wardrobe
• Provide style advice for specific occasions
• Find similar alternatives to items you like
• Work within your budget preferences

💬 **How to Ask:**
• "What should I wear to a job interview?"
• "Find me a casual summer outfit under $200"
• "What goes well with black jeans?"
• "Show me formal dresses for a wedding"

Just describe what you're looking for, and I'll find the perfect pieces for you!"""
    
    @classmethod
    def get_feedback_response(cls) -> str:
        """Get feedback acknowledgment response"""
        return """Thank you for your feedback! I'm constantly learning to provide better style recommendations. 

If you're experiencing any issues or have suggestions, please let me know what specifically you'd like to see improved. 

In the meantime, feel free to ask me for any styling help - I'm here to help you look your best!"""
    
    @classmethod
    def should_skip_expensive_processing(cls, query_type: QueryType) -> bool:
        """Determine if we should skip expensive LLM/vector operations"""
        return query_type in [QueryType.GREETING, QueryType.HELP, QueryType.FEEDBACK]
    
    @classmethod
    def route_query(cls, query: str) -> Dict[str, Any]:
        """
        Main routing function that returns routing decision
        
        Returns:
            Dict with keys:
            - type: QueryType
            - confidence: float
            - skip_processing: bool
            - response: Optional[str] - Direct response if available
        """
        query_type, confidence = cls.classify_query(query)
        
        result = {
            'type': query_type.value,
            'confidence': confidence,
            'skip_processing': cls.should_skip_expensive_processing(query_type),
            'response': None
        }
        
        # Add direct responses for certain query types
        if query_type == QueryType.GREETING:
            result['response'] = cls.get_greeting_response()
        elif query_type == QueryType.HELP:
            result['response'] = cls.get_help_response()
        elif query_type == QueryType.FEEDBACK:
            result['response'] = cls.get_feedback_response()
        
        logger.info(f"Query routed: type={query_type.value}, confidence={confidence:.2f}, skip={result['skip_processing']}")
        
        return result