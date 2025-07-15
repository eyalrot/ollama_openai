#!/usr/bin/env python3
"""
Batch processing example for multiple prompts.
Demonstrates concurrent processing and error handling.
"""

import asyncio
import time
from typing import Any, Dict, List

import aiohttp

# Configuration
PROXY_URL = "http://localhost:11434"
MODEL = "gpt-3.5-turbo"

# Example prompts for batch processing
PROMPTS = [
    "Summarize the theory of relativity in 50 words",
    "List 5 benefits of regular exercise",
    "Explain photosynthesis to a 5-year-old",
    "What are the main causes of climate change?",
    "Describe the water cycle in simple terms",
]


async def generate_single(
    session: aiohttp.ClientSession, prompt: str, index: int
) -> Dict[str, Any]:
    """Generate response for a single prompt."""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 100},
    }

    try:
        start_time = time.time()

        async with session.post(
            f"{PROXY_URL}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:

            if response.status == 200:
                result = await response.json()
                elapsed = time.time() - start_time

                return {
                    "index": index,
                    "prompt": prompt,
                    "response": result.get("response", ""),
                    "success": True,
                    "elapsed_time": elapsed,
                    "tokens": result.get("eval_count", 0),
                }
            else:
                error_text = await response.text()
                return {
                    "index": index,
                    "prompt": prompt,
                    "response": f"Error {response.status}: {error_text}",
                    "success": False,
                    "elapsed_time": 0,
                    "tokens": 0,
                }

    except asyncio.TimeoutError:
        return {
            "index": index,
            "prompt": prompt,
            "response": "Request timed out",
            "success": False,
            "elapsed_time": 30,
            "tokens": 0,
        }
    except Exception as e:
        return {
            "index": index,
            "prompt": prompt,
            "response": f"Error: {str(e)}",
            "success": False,
            "elapsed_time": 0,
            "tokens": 0,
        }


async def process_batch(
    prompts: List[str], max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """Process multiple prompts with concurrency limit."""

    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_generate(session, prompt, index):
        async with semaphore:
            return await generate_single(session, prompt, index)

    # Create session and process all prompts
    async with aiohttp.ClientSession() as session:
        tasks = [
            bounded_generate(session, prompt, i) for i, prompt in enumerate(prompts)
        ]

        results = await asyncio.gather(*tasks)

    return results


def print_results(results: List[Dict[str, Any]]):
    """Pretty print the batch results."""

    total_tokens = 0
    total_time = 0
    successful = 0

    print("\n" + "=" * 80)
    print("BATCH PROCESSING RESULTS")
    print("=" * 80)

    for result in sorted(results, key=lambda x: x["index"]):
        print(f"\n[{result['index'] + 1}] Prompt: {result['prompt'][:50]}...")

        if result["success"]:
            print(f"Response: {result['response'][:200]}...")
            print(f"Time: {result['elapsed_time']:.2f}s | Tokens: {result['tokens']}")
            total_tokens += result["tokens"]
            total_time += result["elapsed_time"]
            successful += 1
        else:
            print(f"ERROR: {result['response']}")

        print("-" * 40)

    print(f"\n{'SUMMARY':^80}")
    print("=" * 80)
    print(f"Total prompts: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Total tokens: {total_tokens}")
    print(f"Average time per request: {total_time/max(successful, 1):.2f}s")
    print(f"Total processing time: {max(r['elapsed_time'] for r in results):.2f}s")


async def main():
    """Main execution."""

    print(f"Processing {len(PROMPTS)} prompts with max 3 concurrent requests...")
    print(f"Using model: {MODEL}")
    print(f"Proxy URL: {PROXY_URL}")

    start_time = time.time()

    # Process batch
    results = await process_batch(PROMPTS, max_concurrent=3)

    total_time = time.time() - start_time

    # Print results
    print_results(results)

    print(f"\nTotal execution time: {total_time:.2f}s")
    print(
        f"Time saved by concurrent processing: "
        f"{sum(r['elapsed_time'] for r in results) - total_time:.2f}s"
    )


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
