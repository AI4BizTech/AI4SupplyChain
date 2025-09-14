#!/usr/bin/env python3
"""
Test runner with coverage reporting for AI4SupplyChain
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description="", check=True, capture_output=False):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        if capture_output and result.stdout:
            return result.stdout.strip()
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if capture_output and e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def check_test_dependencies():
    """Check if test dependencies are available"""
    print("🔍 Checking test dependencies...")
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} found")
    except ImportError:
        print("❌ pytest not found. Installing...")
        if not run_command("uv add --dev pytest pytest-cov pytest-asyncio", "Installing pytest"):
            return False
    
    # Check if coverage is available
    try:
        import coverage
        print(f"✅ coverage {coverage.__version__} found")
    except ImportError:
        print("❌ coverage not found. Installing...")
        if not run_command("uv add --dev coverage", "Installing coverage"):
            return False
    
    return True


def run_unit_tests(test_path="tests/", verbose=False, coverage=False):
    """Run unit tests with optional coverage"""
    print(f"\n🧪 Running unit tests from {test_path}...")
    
    # Build pytest command
    cmd_parts = ["uv run python -m pytest"]
    cmd_parts.append(test_path)
    
    if verbose:
        cmd_parts.append("-v")
    
    if coverage:
        cmd_parts.extend([
            "--cov=ai4supplychain",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])
    
    # Add other useful options
    cmd_parts.extend([
        "--tb=short",  # Shorter traceback format
        "-x",          # Stop on first failure
        "--strict-markers",  # Strict marker checking
    ])
    
    command = " ".join(cmd_parts)
    result = run_command(command, f"Running tests with {'coverage' if coverage else 'basic'} reporting")
    
    if coverage and result:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    return result


def run_specific_test_suite(suite_name):
    """Run specific test suite"""
    test_files = {
        "models": "tests/test_models.py",
        "services": "tests/test_services.py", 
        "agent": "tests/test_agent.py",
        "api": "tests/test_api.py",
        "ui": "tests/test_ui.py",
        "basic": "tests/test_basic.py"
    }
    
    if suite_name not in test_files:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(test_files.keys())}")
        return False
    
    test_file = test_files[suite_name]
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    return run_unit_tests(test_file, verbose=True)


def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running integration tests...")
    
    # Integration tests would test full workflows
    integration_tests = [
        "tests/test_api.py::TestAPIIntegration",
        "tests/test_services.py::TestServiceIntegration"
    ]
    
    for test in integration_tests:
        if Path(test.split("::")[0]).exists():
            result = run_command(
                f"uv run python -m pytest {test} -v",
                f"Running {test}"
            )
            if not result:
                return False
    
    return True


def run_performance_tests():
    """Run performance/load tests"""
    print("\n⚡ Running performance tests...")
    
    # Example performance tests
    perf_commands = [
        # Test database performance
        "uv run python -c \"from src.services.simulation import SimulationService; import time; start=time.time(); s=SimulationService(); s.generate_sample_transactions(1000, [], []); print(f'Generated 1000 transactions in {time.time()-start:.2f}s')\"",
        
        # Test API response time
        "uv run python -c \"import requests; import time; start=time.time(); requests.get('http://localhost:8000/health', timeout=5); print(f'API health check: {time.time()-start:.3f}s')\" 2>/dev/null || echo 'API not running - skipping API performance test'"
    ]
    
    for cmd in perf_commands:
        run_command(cmd, "Performance test", check=False)
    
    return True


def lint_code():
    """Run code linting"""
    print("\n🔍 Running code linting...")
    
    # Check if linting tools are available
    linting_commands = [
        ("uv add --dev flake8", "Installing flake8"),
        ("uv run flake8 ai4supplychain --max-line-length=120 --ignore=E203,W503", "Running flake8 linting"),
    ]
    
    for cmd, desc in linting_commands:
        result = run_command(cmd, desc, check=False)
        if "flake8" in cmd and not result:
            print("⚠️ Linting issues found. Check output above.")
    
    return True


def format_code():
    """Format code using black"""
    print("\n🎨 Formatting code...")
    
    format_commands = [
        ("uv add --dev black", "Installing black"),
        ("uv run black ai4supplychain tests scripts --line-length=120", "Formatting code with black"),
    ]
    
    for cmd, desc in format_commands:
        run_command(cmd, desc, check=False)
    
    return True


def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📄 Generating test report...")
    
    # Run tests with detailed output
    report_cmd = [
        "uv run python -m pytest",
        "tests/",
        "--cov=ai4supplychain",
        "--cov-report=html:test_reports/coverage",
        "--cov-report=xml:test_reports/coverage.xml",
        "--junitxml=test_reports/junit.xml",
        "-v",
        "--tb=long"
    ]
    
    # Create reports directory
    Path("test_reports").mkdir(exist_ok=True)
    
    command = " ".join(report_cmd)
    result = run_command(command, "Generating comprehensive test report")
    
    if result:
        print("\n📊 Test reports generated:")
        print("   - Coverage HTML: test_reports/coverage/index.html")
        print("   - Coverage XML: test_reports/coverage.xml")
        print("   - JUnit XML: test_reports/junit.xml")
    
    return result


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="AI4SupplyChain test runner")
    parser.add_argument("--suite", choices=["models", "services", "agent", "api", "ui", "basic"], 
                       help="Run specific test suite")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--format", action="store_true", help="Format code with black")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_test_dependencies():
        print("❌ Test dependencies not available")
        return 1
    
    success = True
    
    if args.suite:
        success = run_specific_test_suite(args.suite)
    elif args.integration:
        success = run_integration_tests()
    elif args.performance:
        success = run_performance_tests()
    elif args.lint:
        success = lint_code()
    elif args.format:
        success = format_code()
    elif args.report:
        success = generate_test_report()
    elif args.all:
        print("🚀 Running comprehensive test suite...")
        success = (
            run_unit_tests(coverage=True, verbose=args.verbose) and
            run_integration_tests() and
            lint_code() and
            generate_test_report()
        )
        if success:
            print("\n🎉 All tests and checks completed successfully!")
    else:
        # Default: run unit tests
        success = run_unit_tests(coverage=args.coverage, verbose=args.verbose)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
