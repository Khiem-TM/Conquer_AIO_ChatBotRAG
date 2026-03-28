#!/usr/bin/env python
"""Quick start guide - Run this after setup to verify everything works."""

import sys
import subprocess
import time
from pathlib import Path


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_python_version() -> bool:
    """Check Python version."""
    print_section("1️⃣  Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required")
        return False

    print("✅ Python version OK")
    return True


def check_dependencies() -> bool:
    """Check if required packages are installed."""
    print_section("2️⃣  Checking Dependencies")

    required = {
        "fastapi": "FastAPI framework",
        "uvicorn": "ASGI server",
        "pydantic": "Data validation",
        "httpx": "HTTP client",
        "langchain": "NLP utilities",
    }

    all_ok = True
    for package, description in required.items():
        try:
            __import__(package)
            print(f"✅ {package:15} - {description}")
        except ImportError:
            print(f"❌ {package:15} - {description}")
            all_ok = False

    return all_ok


def check_ollama() -> bool:
    """Check if Ollama is running."""
    print_section("3️⃣  Checking Ollama Connection")

    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running on localhost:11434")
            data = response.json()
            models = data.get("models", [])
            print(f"   Available models: {len(models)}")
            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0) // (1024 * 1024 * 1024)
                print(f"   • {name:20} ({size}GB)")
            return True
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False


def check_data_files() -> bool:
    """Check if data files exist."""
    print_section("4️⃣  Checking Data Files")

    data_input = Path("data_input")
    if not data_input.exists():
        print(f"⚠️  {data_input} directory not found (creating...)")
        data_input.mkdir(exist_ok=True)

    files = list(data_input.glob("*"))
    if files:
        print(f"✅ Found {len(files)} document(s) in data_input/:")
        for f in files[:5]:  # Show first 5
            print(f"   • {f.name}")
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more")
        return True
    else:
        print("⚠️  No documents in data_input/")
        print("   Place your documents there before running ingest")
        return True  # Not critical for MVP


def check_config() -> bool:
    """Check environment configuration."""
    print_section("5️⃣  Checking Configuration")

    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env file found")
        # Read and show key settings
        with open(env_file) as f:
            for line in f:
                if line.startswith(("APP_", "OLLAMA_", "CORS_")):
                    print(f"   {line.strip()}")
        return True
    else:
        print("⚠️  .env file not found")
        print("   Using default configuration (should work)")
        return True


def suggest_next_steps() -> None:
    """Print next steps."""
    print_section("🚀 Next Steps")

    print("""
1. Start the FastAPI server:
   python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

2. In another terminal, test the API:
   python test_api_comprehensive.py

3. Or manually test individual endpoints:
   curl http://localhost:8000/health
   
   curl -X POST http://localhost:8000/api/v1/chat \\
     -H "Content-Type: application/json" \\
     -d '{"question": "What is Anscombe quartet?"}'

4. Read the full documentation:
   cat MVP_API_GUIDE_EXTENDED.py | less
   
5. Start your React frontend:
   cd ../frontend  (or wherever your React app is)
   npm install
   npm start

📍 API will be available at: http://localhost:8000
📍 Swagger UI at: http://localhost:8000/docs
""")


def main() -> None:
    """Run all checks."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  RAG CHATBOT BACKEND - MVP SETUP VERIFICATION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Ollama Connection", check_ollama),
        ("Data Files", check_data_files),
        ("Configuration", check_config),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error during {name}: {e}")
            results.append((name, False))

    # Summary
    print_section("📊 Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n✅ All systems ready! Proceeding to next steps...\n")
        suggest_next_steps()
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("   Most common issue: Ollama not running")
        print("   Solution: In a new terminal, run: ollama serve")
        sys.exit(1)


if __name__ == "__main__":
    main()
