#!/usr/bin/env python3
"""
Test OpenRouter free models without model mapping - using full model names directly.
"""

from ollama import Client

client = Client(host='http://localhost:11434')

# Full OpenRouter free model names
openrouter_free_models = [
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free", 
    "microsoft/phi-3-mini-128k-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "gryphe/mythomax-l2-13b:free",
    "undi95/toppy-m-7b:free",
    "openrouter/cinematika-7b:free",
    "upstage/solar-10.7b-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

def test_direct_model_names():
    """Test using full OpenRouter model names directly without mapping."""
    print("Testing OpenRouter Free Models - Direct Names (No Mapping)")
    print("=" * 65)
    
    successful_models = []
    failed_models = []
    
    for model_name in openrouter_free_models:
        print(f"\nTesting: {model_name}")
        print("-" * 50)
        
        try:
            response = client.generate(
                model=model_name,
                prompt='What is AI? Answer in one short sentence.',
                options={
                    'temperature': 0.7,
                    'num_predict': 50
                }
            )
            
            print(f"✅ SUCCESS")
            print(f"Response: {response['response'].strip()}")
            print(f"Tokens: {response.get('eval_count', 'N/A')}")
            successful_models.append(model_name)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ FAILED")
            
            # Parse error types
            if "Rate limit exceeded" in error_msg:
                print("   Reason: Rate limit (1 req/min for free models)")
                failed_models.append((model_name, "Rate Limited"))
            elif "No endpoints found" in error_msg:
                print("   Reason: Model not available")
                failed_models.append((model_name, "Not Available"))
            elif "not a valid model ID" in error_msg:
                print("   Reason: Invalid model ID")
                failed_models.append((model_name, "Invalid ID"))
            else:
                print(f"   Reason: {error_msg[:100]}...")
                failed_models.append((model_name, "Other Error"))
    
    # Summary
    print(f"\n{'=' * 65}")
    print(f"SUMMARY: {len(successful_models)}/{len(openrouter_free_models)} models working")
    print(f"{'=' * 65}")
    
    if successful_models:
        print(f"\n✅ WORKING MODELS ({len(successful_models)}):")
        for model in successful_models:
            print(f"   - {model}")
    
    if failed_models:
        print(f"\n❌ FAILED MODELS ({len(failed_models)}):")
        for model, reason in failed_models:
            print(f"   - {model} ({reason})")
    
    print(f"\n🔍 MODEL MAPPING STATUS: DISABLED (using direct model names)")
    return successful_models

if __name__ == "__main__":
    working_models = test_direct_model_names()
    print(f"\nRecommended for testing: {working_models[0] if working_models else 'None working'}")