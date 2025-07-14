#!/usr/bin/env python3
"""
Test script for OpenRouter free models using Ollama SDK
with the Ollama to OpenAI proxy.
"""

from ollama import Client
import json

# Initialize client pointing to the proxy
client = Client(host='http://localhost:11434')

# Free models to test
free_models = [
    "google/gemma-2-9b-it:free",
    "microsoft/phi-3-mini-128k-instruct:free", 
    "qwen/qwen-2-7b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free"
]

def test_model(model_name):
    """Test a specific model with a simple prompt."""
    print(f"\n{'='*50}")
    print(f"Testing model: {model_name}")
    print(f"{'='*50}")
    
    try:
        response = client.generate(
            model=model_name,
            prompt='Explain what artificial intelligence is in one sentence.',
            options={
                'temperature': 0.7,
                'num_predict': 100  # max_tokens equivalent
            }
        )
        
        print(f"Response: {response['response']}")
        print(f"Tokens used: {response.get('eval_count', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"Error with {model_name}: {e}")
        return False

def main():
    print("Testing OpenRouter Free Models via Ollama Proxy")
    print("=" * 60)
    
    successful_tests = 0
    total_tests = len(free_models)
    
    for model in free_models:
        if test_model(model):
            successful_tests += 1
    
    print(f"\n{'='*60}")
    print(f"Test Summary: {successful_tests}/{total_tests} models working")
    print(f"{'='*60}")
    
    # Test model mapping if available
    print(f"\n{'='*50}")
    print("Testing mapped model names")
    print(f"{'='*50}")
    
    try:
        response = client.generate(
            model='gemma:free',  # This should map to google/gemma-2-9b-it:free
            prompt='What is 2+2?'
        )
        print(f"Mapped model 'gemma:free' response: {response['response']}")
    except Exception as e:
        print(f"Model mapping test failed: {e}")

if __name__ == "__main__":
    main()