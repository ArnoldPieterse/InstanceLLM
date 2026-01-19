"""
Test script for instance management API endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_list_models():
    """Test /list-models endpoint"""
    print("\n=== Test 1: List Models ===")
    try:
        response = requests.get(f"{BASE_URL}/list-models")
        print(f"Status: {response.status_code}")
        print(f"Models: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_instance(port=8003):
    """Test /create-instance endpoint"""
    print(f"\n=== Test 2: Create Instance on Port {port} ===")
    try:
        data = {
            "name": f"Test Instance {port}",
            "port": port,
            "model": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        }
        response = requests.post(f"{BASE_URL}/create-instance", json=data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_start_instance(instance_id, port, model):
    """Test /start-instance endpoint"""
    print(f"\n=== Test 3: Start Instance {instance_id} ===")
    try:
        data = {
            "instance_id": instance_id,
            "port": port,
            "model": model
        }
        response = requests.post(f"{BASE_URL}/start-instance", json=data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_instances():
    """Test /list-instances endpoint"""
    print("\n=== Test 4: List Running Instances ===")
    try:
        response = requests.get(f"{BASE_URL}/list-instances")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Instances: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_stop_instance(instance_id):
    """Test /stop-instance endpoint"""
    print(f"\n=== Test 5: Stop Instance {instance_id} ===")
    try:
        data = {
            "instance_id": instance_id,
            "port": 0  # Optional
        }
        response = requests.post(f"{BASE_URL}/stop-instance", json=data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Instance Management API Test Suite")
    print("=" * 60)
    
    # Test 1: List models
    test_list_models()
    
    # Test 2: Create a new instance
    if test_create_instance(8004):
        time.sleep(3)  # Wait for instance to start
        
        # Test 3: Try to start an already running instance (should return error)
        test_start_instance("instance-8004", 8004, "Llama-3.2-3B-Instruct-Q4_K_M.gguf")
    
    # Test 4: List all instances
    test_list_instances()
    
    # Test 5: Stop the instance we created
    time.sleep(2)
    test_stop_instance("instance-8004")
    
    # Verify it stopped
    time.sleep(1)
    test_list_instances()
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
