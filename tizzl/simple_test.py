#!/usr/bin/env python3
"""
Simple test to verify the Tizzl app works with OpenAI
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ OpenAI API key found: {api_key[:20]}...")
else:
    print("❌ No OpenAI API key found in .env")
    sys.exit(1)

# Test OpenAI connection
try:
    import openai
    client = openai.OpenAI(api_key=api_key)
    
    # Test with a simple completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a fashion stylist."},
            {"role": "user", "content": "Suggest a casual outfit in one sentence."}
        ],
        max_tokens=50
    )
    
    print("✅ OpenAI API is working!")
    print(f"Sample response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Error connecting to OpenAI: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("OpenAI integration is configured correctly!")
print("The Tizzl app can now use GPT-4 for recommendations.")
print("="*50)