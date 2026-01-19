"""
Test client for the Local LLM Server
"""

import requests
import json
import sys


def test_health(base_url="http://localhost:8000"):
    """Test the health endpoint."""
    print("Testing /health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_prompt(base_url="http://localhost:8000", prompt="What is 2+2?"):
    """Test the prompt endpoint."""
    print(f"Testing /prompt endpoint with: '{prompt}'")
    response = requests.post(
        f"{base_url}/prompt",
        json={
            "prompt": prompt,
            "temperature": 0.7,
            "max_tokens": 100
        }
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        print(f"Model: {data['model_path']}")
        print(f"Config: {json.dumps(data['config_used'], indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()


def test_stream(base_url="http://localhost:8000", prompt="Count from 1 to 5"):
    """Test the streaming endpoint."""
    print(f"Testing /stream endpoint with: '{prompt}'")
    response = requests.post(
        f"{base_url}/stream",
        json={
            "prompt": prompt,
            "temperature": 0.8,
            "max_tokens": 200
        },
        stream=True
    )
    
    print(f"Status Code: {response.status_code}")
    print("Streaming response:")
    print("-" * 50)
    
    if response.status_code == 200:
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                print(chunk, end='', flush=True)
        print()
        print("-" * 50)
    else:
        print(f"Error: {response.text}")
    print()


def test_custom_params(base_url="http://localhost:8000"):
    """Test with custom generation parameters."""
    print("Testing with custom parameters...")
    
    test_cases = [
        {
            "prompt": "Write a haiku about coding",
            "temperature": 0.9,
            "max_tokens": 50
        },
        {
            "prompt": "Explain Python in one sentence",
            "temperature": 0.5,
            "max_tokens": 100
        },
        {
            "prompt": "List 3 programming languages",
            "temperature": 0.3,
            "max_tokens": 50,
            "top_p": 0.9
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test['prompt']}")
        response = requests.post(f"{base_url}/prompt", json=test)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['response']}")
        else:
            print(f"Error: {response.text}")
    print()


def interactive_mode(base_url="http://localhost:8000"):
    """Interactive mode for testing."""
    print("Interactive Mode")
    print("Type your prompts (or 'quit' to exit)")
    print("-" * 50)
    
    while True:
        prompt = input("\nYou: ").strip()
        
        if prompt.lower() in ['quit', 'exit', 'q']:
            break
        
        if not prompt:
            continue
        
        try:
            response = requests.post(
                f"{base_url}/prompt",
                json={
                    "prompt": prompt,
                    "temperature": 0.7,
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nAssistant: {data['response']}")
            else:
                print(f"\nError: {response.text}")
        
        except Exception as e:
            print(f"\nError: {e}")


def main():
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing LLM Server at: {base_url}")
    print("=" * 60)
    print()
    
    try:
        # Run all tests
        test_health(base_url)
        test_prompt(base_url, "What is the capital of France?")
        test_prompt(base_url, "Write a one-line joke about programming")
        test_stream(base_url, "Explain machine learning in 2 sentences")
        test_custom_params(base_url)
        
        # Interactive mode
        choice = input("\nEnter interactive mode? (y/n): ").strip().lower()
        if choice == 'y':
            interactive_mode(base_url)
    
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to server at {base_url}")
        print("Make sure the server is running.")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
