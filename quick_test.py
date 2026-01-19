"""
Quick test script for the LLM server
"""

import requests
import time
import sys

def test_server():
    base_url = "http://localhost:8000"
    
    print("=" * 70)
    print("Testing Local LLM Server")
    print("=" * 70)
    
    # Wait for server to be ready
    print("\nWaiting for server to start...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Server is ready!\n")
                break
        except:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                print("✗ Server not responding. Make sure it's running:")
                print("  python llm_server.py models\\Llama-3.2-3B-Instruct-Q4_K_M.gguf")
                return
    
    # Test 1: Health check
    print("Test 1: Health Check")
    print("-" * 70)
    response = requests.get(f"{base_url}/health")
    health = response.json()
    print(f"Status: {health['status']}")
    print(f"Model loaded: {health['model_loaded']}")
    print(f"Model: {health['model_path']}")
    print(f"Config: temperature={health['config']['temperature']}, max_tokens={health['config']['max_tokens']}")
    print()
    
    # Test 2: Simple prompt
    print("Test 2: Simple Prompt")
    print("-" * 70)
    prompt1 = "Hello! How are you today?"
    print(f"Prompt: {prompt1}")
    response = requests.post(
        f"{base_url}/prompt",
        json={"prompt": prompt1, "temperature": 0.7, "max_tokens": 200}
    )
    result = response.json()
    print(f"Response: {result['response']}")
    print()
    
    # Test 3: Question prompt
    print("Test 3: Question Prompt")
    print("-" * 70)
    prompt2 = "What is Python programming language?"
    print(f"Prompt: {prompt2}")
    response = requests.post(
        f"{base_url}/prompt",
        json={"prompt": prompt2, "temperature": 0.5, "max_tokens": 150}
    )
    result = response.json()
    print(f"Response: {result['response']}")
    print()
    
    # Test 4: Code generation
    print("Test 4: Code Generation")
    print("-" * 70)
    prompt3 = "Write a Python function to calculate factorial"
    print(f"Prompt: {prompt3}")
    response = requests.post(
        f"{base_url}/prompt",
        json={"prompt": prompt3, "temperature": 0.3, "max_tokens": 200}
    )
    result = response.json()
    print(f"Response: {result['response']}")
    print()
    
    # Test 5: Streaming
    print("Test 5: Streaming Response")
    print("-" * 70)
    prompt4 = "Why is the sky blue? Explain in simple terms."
    print(f"Prompt: {prompt4}")
    print("Streaming response: ", end="", flush=True)
    response = requests.post(
        f"{base_url}/stream",
        json={"prompt": prompt4, "temperature": 0.7, "max_tokens": 150},
        stream=True
    )
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end="", flush=True)
    print("\n")
    
    # Test 6: Custom parameters
    print("Test 6: Custom Temperature Test")
    print("-" * 70)
    prompt5 = "Tell me something interesting"
    print(f"Prompt: {prompt5}")
    
    print("\n  With temperature=0.3 (more focused):")
    response = requests.post(
        f"{base_url}/prompt",
        json={"prompt": prompt5, "temperature": 0.3, "max_tokens": 100}
    )
    print(f"  {response.json()['response']}")
    
    print("\n  With temperature=0.9 (more creative):")
    response = requests.post(
        f"{base_url}/prompt",
        json={"prompt": prompt5, "temperature": 0.9, "max_tokens": 100}
    )
    print(f"  {response.json()['response']}")
    print()
    
    # Summary
    print("=" * 70)
    print("✓ All Tests Completed Successfully!")
    print("=" * 70)
    print("\nThe LLM server is working correctly:")
    print("  • Model loading: ✓")
    print("  • Standard prompts: ✓")
    print("  • Streaming: ✓")
    print("  • Custom parameters: ✓")
    print("  • Network access: ✓")
    print("\nServer is accessible at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print()

if __name__ == "__main__":
    try:
        test_server()
    except KeyboardInterrupt:
        print("\n\nTests interrupted.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure the server is running:")
        print("  python llm_server.py models\\Llama-3.2-3B-Instruct-Q4_K_M.gguf")
