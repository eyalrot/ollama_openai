#!/usr/bin/env python3
"""
Example of using the Ollama OpenAI proxy with LangChain.
Demonstrates how to integrate with popular LLM frameworks.
"""

# Note: Install langchain first: pip install langchain langchain-community

from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import HumanMessage, SystemMessage

# Configure to use the proxy
PROXY_BASE_URL = "http://localhost:11434"

# Example 1: Simple LLM usage
print("=== Simple LLM Example ===")
llm = Ollama(
    base_url=PROXY_BASE_URL,
    model="gpt-3.5-turbo"
)

response = llm.invoke("What are the three laws of robotics?")
print(response)

# Example 2: Chat model with messages
print("\n=== Chat Model Example ===")
chat = ChatOllama(
    base_url=PROXY_BASE_URL,
    model="gpt-3.5-turbo"
)

messages = [
    SystemMessage(content="You are a helpful coding assistant."),
    HumanMessage(content="Write a Python function to calculate fibonacci numbers")
]

response = chat.invoke(messages)
print(response.content)

# Example 3: Using prompt templates and chains
print("\n=== Prompt Template Example ===")
template = """You are a {profession} expert. 
Answer the following question in a {style} manner:

Question: {question}

Answer:"""

prompt = PromptTemplate(
    input_variables=["profession", "question", "style"],
    template=template
)

chain = LLMChain(llm=llm, prompt=prompt)

response = chain.invoke({
    "profession": "astronomy",
    "question": "Why do stars twinkle?",
    "style": "simple and educational"
})
print(response['text'])

# Example 4: Streaming with callback
print("\n=== Streaming Example ===")
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

streaming_llm = Ollama(
    base_url=PROXY_BASE_URL,
    model="gpt-3.5-turbo",
    callbacks=[StreamingStdOutCallbackHandler()]
)

print("Response: ", end='', flush=True)
response = streaming_llm.invoke("Write a short poem about Python programming")
print()  # New line after streaming

# Example 5: Custom model mapping
print("\n=== Custom Model Mapping ===")
# If you have model mappings configured
try:
    custom_llm = Ollama(
        base_url=PROXY_BASE_URL,
        model="llama2"  # This will be mapped to actual model
    )
    
    response = custom_llm.invoke("What is machine learning?")
    print(response)
except Exception as e:
    print(f"Custom model example failed: {e}")
    print("Ensure model mappings are configured in the proxy")