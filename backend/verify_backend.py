import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_backend():
    print("Starting Backend Verification...")
    
    # 1. Register a new user
    email = f"test_{int(time.time())}@example.com"
    password = "password123"
    name = "Test User"
    
    print(f"1. Registering user {email}...")
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email, "password": password, "name": name
        })
        if resp.status_code == 200:
            print("   [PASS] Registration successful")
            token = resp.json()["access_token"]
        else:
            print(f"   [FAIL] Registration failed: {resp.text}")
            return
    except Exception as e:
        print(f"   [FAIL] Connection error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Me Endpoint
    print("2. Testing /api/auth/me...")
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if resp.status_code == 200:
        print("   [PASS] Me endpoint working")
    else:
        print(f"   [FAIL] Me endpoint failed: {resp.text}")

    # 3. Test Chat Endpoint
    print("3. Testing /api/chat...")
    chat_payload = {"message": "Hello, are you working?", "history": []}
    resp = requests.post(f"{BASE_URL}/api/chat", json=chat_payload, headers=headers)
    if resp.status_code == 200:
        print("   [PASS] Chat endpoint working")
        print(f"   Response: {resp.json().get('response')[:50]}...")
    else:
        print(f"   [FAIL] Chat endpoint failed: {resp.text}")

    # 4. Test Circuit Run Endpoint
    print("4. Testing /api/circuit/run...")
    # Simple circuit: H on 0
    circuit = [{"name": "h", "qubits": [0], "params": []}]
    resp = requests.post(f"{BASE_URL}/api/circuit/run", json={
        "circuit": circuit,
        "num_qubits": 2,
        "use_noise": False
    }, headers=headers)
    
    if resp.status_code == 200:
        print("   [PASS] Circuit run working")
    else:
        print(f"   [FAIL] Circuit run failed: {resp.text}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    test_backend()
