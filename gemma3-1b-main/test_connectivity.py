"""
DNS and Service Connectivity Test Script
Run this to diagnose connection issues before running command_script.py
"""

import requests
import os
import socket

# Check environment configuration
RUNNING_IN_CLUSTER = os.getenv("RUNNING_IN_CLUSTER", "false").lower() == "true"

print("=" * 60)
print("Service Connectivity Test")
print("=" * 60)
print(f"Running in cluster mode: {RUNNING_IN_CLUSTER}")
print()

# Define endpoints based on mode
if RUNNING_IN_CLUSTER:
    endpoints = {
        "promptimizer": "http://promptimizer-service:11434/api/generate",
        "llama": "http://llama-service:11434/api/generate",
        "qwen": "http://qwen-service:11434/api/generate",
        "qwen_small": "http://qwen-small-service:11434/api/generate",
        "judge": "http://judge-service:11434/api/generate",
    }
else:
    endpoints = {
        "promptimizer": os.getenv("PROMPTIMIZER_URL", "http://localhost:11434/api/generate"),
        "llama": os.getenv("LLAMA_URL", "http://localhost:11435/api/generate"),
        "qwen": os.getenv("QWEN_URL", "http://localhost:11436/api/generate"),
        "qwen_small": os.getenv("QWEN_SMALL_URL", "http://localhost:11437/api/generate"),
        "judge": os.getenv("JUDGE_URL", "http://localhost:11438/api/generate"),
    }

print("Testing endpoints:")
print()

# Test each endpoint
for service_name, url in endpoints.items():
    print(f"Testing {service_name}...")
    print(f"  URL: {url}")
    
    # Extract host and port from URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80
        
        # Test DNS resolution
        try:
            ip_address = socket.gethostbyname(host)
            print(f"  ✓ DNS resolves: {host} -> {ip_address}")
        except socket.gaierror as e:
            print(f"  ✗ DNS FAILED: Cannot resolve {host}")
            print(f"    Error: {e}")
            print()
            continue
        
        # Test TCP connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"  ✓ Port {port} is open")
            else:
                print(f"  ✗ Port {port} is CLOSED or FILTERED")
                print()
                continue
        except Exception as e:
            print(f"  ✗ Connection test failed: {e}")
            print()
            continue
        
        # Test HTTP endpoint
        try:
            # Try to hit the version endpoint instead of generate
            version_url = url.replace('/api/generate', '/api/version')
            response = requests.get(version_url, timeout=5)
            print(f"  ✓ HTTP endpoint responds (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ HTTP endpoint test failed: {e}")
            print(f"    (Service might still work for POST requests)")
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
    
    print()

print("=" * 60)
print("Test complete!")
print()

if RUNNING_IN_CLUSTER:
    print("Running in CLUSTER mode.")
    print("If tests fail, check:")
    print("  - kubectl get pods (are all pods running?)")
    print("  - kubectl get services (are services created?)")
    print("  - kubectl logs deployment/[service-name] (any errors?)")
else:
    print("Running in LOCAL mode.")
    print("If tests fail, check:")
    print("  - Are port-forwards active? (kubectl port-forward ...)")
    print("  - Are environment variables set correctly?")
    print("  - Is Ollama running on the specified ports?")

print("=" * 60)
