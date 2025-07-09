#!/usr/bin/env python3
"""
Streaming chat example with conversation history.
"""

from ollama import Client
import sys

# Initialize client
client = Client(host='http://localhost:11434')

# Conversation history
messages = [
    {
        'role': 'system',
        'content': 'You are a helpful AI assistant. Keep responses concise.'
    }
]

print("Ollama OpenAI Proxy - Chat Interface")
print("Type 'quit' to exit, 'clear' to reset conversation")
print("-" * 50)

while True:
    # Get user input
    user_input = input("\nYou: ").strip()
    
    if user_input.lower() == 'quit':
        print("Goodbye!")
        break
    
    if user_input.lower() == 'clear':
        messages = messages[:1]  # Keep system message
        print("Conversation cleared.")
        continue
    
    # Add user message
    messages.append({
        'role': 'user',
        'content': user_input
    })
    
    # Stream response
    print("Assistant: ", end='', flush=True)
    
    try:
        # Collect full response for history
        full_response = ""
        
        # Stream the response
        stream = client.chat(
            model='gpt-3.5-turbo',
            messages=messages,
            stream=True
        )
        
        for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                content = chunk['message']['content']
                print(content, end='', flush=True)
                full_response += content
        
        print()  # New line after response
        
        # Add assistant response to history
        messages.append({
            'role': 'assistant',
            'content': full_response
        })
        
        # Keep conversation size manageable
        if len(messages) > 20:
            # Keep system message and last 18 messages
            messages = messages[:1] + messages[-18:]
            
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
        break
    except Exception as e:
        print(f"\nError: {e}")
        # Remove the failed user message
        messages.pop()