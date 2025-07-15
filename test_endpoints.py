#!/usr/bin/env python

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

# Test each endpoint one by one to see which are failing
print("Testing /v1/chat/completions:")
response = client.get("/v1/chat/completions")
print(f"Status: {response.status_code}")

print("\nTesting /v1/models:")
response = client.get("/v1/models")
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Response: {response.text[:200]}")

print("\nTesting /v1/embeddings:")
response = client.get("/v1/embeddings")
print(f"Status: {response.status_code}")
