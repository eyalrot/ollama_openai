#!/usr/bin/env python3
"""
Test model mapping with OpenRouter free models.
"""

from ollama import Client

client = Client(host='http://localhost:11434')

def test_mapping():
    """Test model mapping functionality."""
    print("Testing model mapping with OpenRouter free models\n")
    
    # Test original example models
    test_cases = [
        ("gemma:free", "Should map to google/gemma-2-9b-it:free"),
        ("gpt-3.5-turbo", "Should map to google/gemma-2-9b-it:free"),
        ("google/gemma-2-9b-it:free", "Direct model name (no mapping needed)")
    ]
    
    for model, description in test_cases:
        print(f"Testing: {model}")
        print(f"Description: {description}")
        
        try:
            response = client.generate(
                model=model,
                prompt='Say "Hello, I am working!" in exactly that format.',
                options={'num_predict': 20}
            )
            print(f"✅ SUCCESS: {response['response'].strip()}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_mapping()