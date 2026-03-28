#!/usr/bin/env python3
"""
Comprehensive system check for RAG Chatbot
"""
import os
import sys
import json
import httpx
from datetime import datetime

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ {text}{RESET}")

def check_backend():
    """Check backend server"""
    print_header("BACKEND SERVER CHECK")
    
    try:
        response = httpx.get('http://localhost:8000/health', timeout=5)
        response.raise_for_status()
        data = response.json()
        print_success(f"Backend is running on port 8000")
        print_info(f"Health status: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print_error(f"Backend check failed: {e}")
        return False

def check_ollama_local():
    """Check if Ollama is running locally"""
    print_header("OLLAMA SERVICE CHECK (Local)")
    
    candidates = [
        'http://localhost:11434',
        'http://127.0.0.1:11434',
    ]
    
    for url in candidates:
        try:
            response = httpx.get(f'{url}/api/tags', timeout=5)
            response.raise_for_status()
            data = response.json()
            print_success(f"Ollama is running at {url}")
            models = data.get('models', [])
            if models:
                print_info(f"Available models:")
                for model in models:
                    model_name = model.get('name', 'Unknown')
                    size = model.get('size', 0)
                    size_gb = size / (1024**3)
                    print(f"  - {model_name} ({size_gb:.2f} GB)")
            else:
                print_warning("No models loaded in Ollama")
            return True
        except Exception as e:
            print_warning(f"  {url}: {str(e)[:100]}")
    
    print_error("Ollama is not accessible locally")
    return False

def check_ollama_docker():
    """Check if Ollama Docker container exists"""
    print_header("OLLAMA DOCKER CONTAINER CHECK")
    
    try:
        import subprocess
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'name=ollama', '--format', '{{json .}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            containers = [json.loads(line) for line in result.stdout.strip().split('\n')]
            for container in containers:
                status = container.get('Status', 'Unknown')
                name = container.get('Names', 'Unknown')
                ports = container.get('Ports', 'N/A')
                print_info(f"Container: {name}")
                print_info(f"  Status: {status}")
                print_info(f"  Ports: {ports}")
            return True
        else:
            print_error("No Ollama Docker containers found")
            return False
    except Exception as e:
        print_warning(f"Docker check failed: {e}")
        return False

def check_python_dependencies():
    """Check if required Python packages are installed"""
    print_header("PYTHON DEPENDENCIES CHECK")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'httpx',
        'qdrant_client',
        'langchain',
        'pypdf',
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} is installed")
        except ImportError:
            print_error(f"{package} is NOT installed")
            all_ok = False
    
    return all_ok

def check_environment():
    """Check environment variables"""
    print_header("ENVIRONMENT VARIABLES CHECK")
    
    env_vars = [
        'OLLAMA_BASE_URL',
        'OLLAMA_MODEL',
        'CORS_ORIGINS',
        'PYTHONUNBUFFERED',
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NOT SET')
        if value != 'NOT SET':
            print_success(f"{var} = {value[:100]}")
        else:
            print_warning(f"{var} = NOT SET (using default)")

def test_api_endpoints():
    """Test API endpoints"""
    print_header("API ENDPOINTS TEST")
    
    endpoints = [
        ('GET', 'http://localhost:8000/health', None),
        ('POST', 'http://localhost:8000/api/v1/chat', {'question': 'What is RAG?'}),
        ('GET', 'http://localhost:8000/api/v1/history', None),
    ]
    
    for method, url, data in endpoints:
        try:
            if method == 'GET':
                response = httpx.get(url, timeout=10)
            else:
                response = httpx.post(url, json=data, timeout=10)
            
            status = response.status_code
            if status == 200:
                print_success(f"{method} {url} -> {status}")
            else:
                print_warning(f"{method} {url} -> {status}")
        except Exception as e:
            print_error(f"{method} {url} failed: {str(e)[:80]}")

def main():
    print(f"\n{BLUE}{'#'*60}")
    print(f"  RAG CHATBOT SYSTEM CHECK")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}{RESET}\n")
    
    # Run all checks
    backend_ok = check_backend()
    ollama_local_ok = check_ollama_local()
    ollama_docker_ok = check_ollama_docker()
    deps_ok = check_python_dependencies()
    check_environment()
    test_api_endpoints()
    
    # Summary
    print_header("SYSTEM STATUS SUMMARY")
    
    checks = {
        'Backend Server': backend_ok,
        'Ollama Local': ollama_local_ok,
        'Python Dependencies': deps_ok,
    }
    
    print("\nStatus:")
    for name, status in checks.items():
        symbol = '✓' if status else '✗'
        color = GREEN if status else RED
        print(f"  {color}{symbol} {name}{RESET}")
    
    all_ok = all(checks.values())
    
    if all_ok:
        print(f"\n{GREEN}All checks passed! System is ready.{RESET}\n")
    else:
        print(f"\n{YELLOW}Some checks failed. See details above.{RESET}\n")
        
        if not ollama_local_ok and not ollama_docker_ok:
            print(f"{YELLOW}Ollama is not running. To fix:{RESET}")
            print(f"  Option 1: Run Ollama locally")
            print(f"    ollama serve")
            print(f"  Option 2: Use Docker Compose")
            print(f"    cd docker/ && docker compose up -d ollama")
            print(f"  Option 3: Pull model manually")
            print(f"    ollama pull llama3.1:8b")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
