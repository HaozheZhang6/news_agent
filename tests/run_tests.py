#!/usr/bin/env python3
"""Test runner script for Voice News Agent."""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def main():
    """Main test runner."""
    print("🧪 Voice News Agent Test Runner")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Test commands
    test_commands = [
        ("python -m pytest tests/backend/ -v --tb=short --timeout=15", "Backend API Tests"),
        ("python -m pytest tests/src/ -v --tb=short --timeout=15", "Source Component Tests"),
        ("python -m pytest tests/integration/ -v --tb=short --timeout=15", "Integration Tests"),
        ("python -m pytest tests/ -v --tb=short --durations=10 --timeout=15", "All Tests"),
        ("python -m pytest tests/ -v --tb=short -m 'not slow' --timeout=15", "Fast Tests Only"),
    ]
    
    # Run tests
    success_count = 0
    total_count = len(test_commands)
    
    for command, description in test_commands:
        if run_command(command, description):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary: {success_count}/{total_count} test suites passed")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
