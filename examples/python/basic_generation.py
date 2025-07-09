#!/usr/bin/env python3
"""
Basic text generation example using the Ollama Python SDK
with the Ollama to OpenAI proxy.
"""

from ollama import Client

# Initialize client pointing to the proxy
client = Client(host='http://localhost:11434')

# Example 1: Simple generation
print("=== Simple Generation ===")
response = client.generate(
    model='gpt-3.5-turbo',  # Or your mapped model name
    prompt='Explain quantum computing in one paragraph'
)
print(response['response'])
print(f"\nTokens used: {response.get('eval_count', 'N/A')}")

# Example 2: Generation with parameters
print("\n=== Generation with Parameters ===")
response = client.generate(
    model='gpt-3.5-turbo',
    prompt='Write a haiku about programming',
    options={
        'temperature': 0.7,
        'top_p': 0.9,
        'num_predict': 50  # max_tokens equivalent
    }
)
print(response['response'])

# Example 3: Using model mapping
print("\n=== Using Model Mapping ===")
# If you have "llama2" mapped to an actual model
try:
    response = client.generate(
        model='llama2',  # This gets mapped to the actual model
        prompt='What is the meaning of life?'
    )
    print(response['response'])
except Exception as e:
    print(f"Model mapping example failed: {e}")
    print("Make sure you have model mappings configured!")