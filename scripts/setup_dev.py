#!/usr/bin/env python3
"""
Development environment setup script for AI4SupplyChain
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description="", check=True):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check UV
    if not shutil.which("uv"):
        print("❌ UV package manager not found. Please install UV first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    print("✅ UV package manager found")
    
    # Check Git
    if not shutil.which("git"):
        print("❌ Git not found. Please install Git first.")
        return False
    print("✅ Git found")
    
    return True


def setup_environment():
    """Setup the development environment"""
    print("\n🚀 Setting up AI4SupplyChain development environment...")
    
    if not check_prerequisites():
        return False
    
    # Create virtual environment and install dependencies
    if not run_command("uv sync", "Installing dependencies with UV"):
        return False
    
    # Create .env file from template if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created. Please update it with your API keys.")
    
    # Create storage directories
    storage_dirs = [
        "storage/database",
        "storage/uploads/documents",
        "storage/uploads/imports", 
        "storage/exports/reports",
        "storage/exports/forecasts",
        "storage/exports/backups",
        "storage/logs"
    ]
    
    print("📁 Creating storage directories...")
    for directory in storage_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Storage directories created")
    
    # Initialize database
    print("🗄️ Initializing database...")
    init_result = run_command(
        "uv run python -c \"from src.services.simulation import SimulationService; s = SimulationService(); print(s.initialize_sample_database())\"",
        "Setting up sample database",
        check=False
    )
    
    if init_result:
        print("✅ Database initialized with sample data")
    else:
        print("⚠️ Database initialization failed. You can run it manually later.")
    
    # Run basic tests
    print("🧪 Running basic tests...")
    test_result = run_command("uv run python -m pytest tests/test_basic.py -v", "Running basic tests", check=False)
    
    if test_result:
        print("✅ Basic tests passed")
    else:
        print("⚠️ Some tests failed. Check the output above.")
    
    print("\n🎉 Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    print("2. Run the API server: uv run uvicorn ai4supplychain.api.main:app --reload")
    print("3. Run the UI: uv run streamlit run ai4supplychain/ui/main.py")
    print("4. Run tests: uv run python -m pytest")
    
    return True


def clean_environment():
    """Clean the development environment"""
    print("🧹 Cleaning development environment...")
    
    # Remove virtual environment
    run_command("uv clean", "Cleaning UV cache", check=False)
    
    # Remove storage files (keep directories)
    storage_files = [
        "storage/database/inventory.db",
        "storage/logs/*.log"
    ]
    
    for pattern in storage_files:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file():
                file_path.unlink()
                print(f"🗑️ Removed {file_path}")
    
    print("✅ Environment cleaned")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI4SupplyChain development setup")
    parser.add_argument("--clean", action="store_true", help="Clean the development environment")
    parser.add_argument("--check", action="store_true", help="Only check prerequisites")
    
    args = parser.parse_args()
    
    if args.clean:
        clean_environment()
    elif args.check:
        success = check_prerequisites()
        sys.exit(0 if success else 1)
    else:
        success = setup_environment()
        sys.exit(0 if success else 1)
