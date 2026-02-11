import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_docs():
    print("Testing /docs visibility...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: /docs is accessible.")
        else:
            print(f"FAILURE: /docs returned {response.status_code}")
        
        csp = response.headers.get("Content-Security-Policy", "")
        print(f"CSP: {csp}")
        if "cdn.jsdelivr.net" in csp:
            print("SUCCESS: CSP allows Swagger assets.")
        else:
            print("FAILURE: CSP might block Swagger assets.")
            
    except Exception as e:
        print(f"ERROR: {e}")

def test_cors():
    print("\nTesting CORS headers for production domain...")
    headers = {
        "Origin": "https://quantcai.in",
        "Access-Control-Request-Method": "GET"
    }
    try:
        response = requests.options(f"{BASE_URL}/", headers=headers)
        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        print(f"Access-Control-Allow-Origin: {allow_origin}")
        if allow_origin == "https://quantcai.in":
            print("SUCCESS: CORS allowed for production domain.")
        else:
            print("FAILURE: CORS origin mismatch.")
    except Exception as e:
        print(f"ERROR: {e}")

def test_middleware_error():
    print("\nTesting middleware error handling (should return JSON, not crash)...")
    # We can't easily trigger a crash without modifying code, 
    # but we can verify the middleware is running by checking headers.
    try:
        response = requests.get(f"{BASE_URL}/")
        request_id = response.headers.get("X-Request-ID")
        print(f"X-Request-ID: {request_id}")
        if request_id:
            print("SUCCESS: Middleware is active and adding headers.")
        else:
            print("FAILURE: No X-Request-ID header found.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_docs()
    test_cors()
    test_middleware_error()
