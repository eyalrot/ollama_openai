#!/usr/bin/env python3
"""
Phase 2 Feature: Tool Calling Example

This example demonstrates how to use tool/function calling with the Ollama-OpenAI proxy.
The proxy translates between Ollama and OpenAI tool calling formats seamlessly.
"""

import json
from typing import Any, Dict

from ollama import Client


def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    Mock weather function for demonstration.
    In a real application, this would call a weather API.
    """
    return {
        "location": location,
        "temperature": 22,
        "unit": unit,
        "condition": "sunny",
        "humidity": 60,
        "description": f"The weather in {location} is sunny with a temperature of 22°{unit[0].upper()}",
    }


def calculate_math(expression: str) -> Dict[str, Any]:
    """
    Mock calculation function for demonstration.
    In a real application, this would safely evaluate mathematical expressions.
    """
    try:
        # Simple safe evaluation for demo (DO NOT use eval() in production!)
        result = eval(expression)
        return {"expression": expression, "result": result, "success": True}
    except Exception as e:
        return {"expression": expression, "error": str(e), "success": False}


def main():
    """Demonstrate tool calling with the Ollama-OpenAI proxy."""

    # Initialize client (proxy running on default port)
    client = Client(host="http://localhost:11434")

    # Define available tools/functions
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a specific location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state/country, e.g. 'San Francisco, CA'",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit preference",
                        },
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_math",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },
    ]

    # Example 1: Weather query
    print("=== Example 1: Weather Query ===")
    try:
        response = client.chat(
            model="gpt-4",  # This will be mapped through the proxy
            messages=[{"role": "user", "content": "What's the weather like in Tokyo?"}],
            tools=tools,
        )

        print(f"Response: {response}")

        # Check if the model wants to call a function
        if hasattr(response, "message") and hasattr(response.message, "tool_calls"):
            tool_calls = response.message.tool_calls
            print(f"Model requested {len(tool_calls)} tool calls:")

            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                print(f"  Function: {function_name}")
                print(f"  Arguments: {arguments}")

                # Execute the function
                if function_name == "get_weather":
                    result = get_weather(**arguments)
                    print(f"  Result: {result}")

    except Exception as e:
        print(f"Error in Example 1: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Math calculation
    print("=== Example 2: Math Calculation ===")
    try:
        response = client.chat(
            model="gpt-4",
            messages=[{"role": "user", "content": "Calculate 15 * 23 + 7"}],
            tools=tools,
        )

        print(f"Response: {response}")

        # Process any tool calls
        if hasattr(response, "message") and hasattr(response.message, "tool_calls"):
            tool_calls = response.message.tool_calls
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                print(f"  Function: {function_name}")
                print(f"  Arguments: {arguments}")

                if function_name == "calculate_math":
                    result = calculate_math(**arguments)
                    print(f"  Result: {result}")

    except Exception as e:
        print(f"Error in Example 2: {e}")


if __name__ == "__main__":
    print("Phase 2 Tool Calling Example")
    print("=" * 40)
    print("This example demonstrates tool calling functionality.")
    print("Make sure the Ollama-OpenAI proxy is running on localhost:11434")
    print("and configured with a model that supports tool calling.\n")

    main()
