"""
Test configuration for Ollama SDK compatibility tests.
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Test server configuration
PROXY_HOST = os.getenv("PROXY_HOST", "http://localhost:11434")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "http://localhost:11434/v1")

# Test models
TEST_CHAT_MODELS: List[str] = [
    "gpt-3.5-turbo",
    "gpt-4",
    "llama2",  # If mapped in your configuration
]

TEST_EMBEDDING_MODELS: List[str] = [
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large",
]

# Default test model (should be a model that's always available)
DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"

# Test parameters
TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Performance test settings
PERF_TEST_ITERATIONS = 10
PERF_CONCURRENT_REQUESTS = 5

# Test data
SAMPLE_TEXTS = [
    "The quick brown fox jumps over the lazy dog",
    "Machine learning is a subset of artificial intelligence",
    "Python is a high-level programming language",
    "Testing is an essential part of software development",
    "Embeddings represent text as numerical vectors",
]

UNICODE_TEST_TEXTS = [
    "Hello, 世界! 🌍",  # Mixed languages with emoji
    "Привет мир",  # Cyrillic
    "مرحبا بالعالم",  # Arabic
    "Γειά σου κόσμε",  # Greek
    "🚀💻🔬",  # Emojis only
]

LONG_TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis 
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore 
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt 
in culpa qui officia deserunt mollit anim id est laborum.
""" * 50  # Approximately 2500 words

# Expected embedding dimensions for known models
EXPECTED_DIMENSIONS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

# Error test cases
INVALID_MODELS = [
    "non-existent-model",
    "fake-embedding-model",
    "",  # Empty model name
]

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"