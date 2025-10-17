#!/usr/bin/env python3
"""
Automated VAD and Interruption Test Runner

Runs comprehensive tests for:
- Backend VAD validation
- Interruption flow
- End-to-end WebSocket integration

Usage:
    python tests/run_vad_tests.py [options]

Options:
    --vad-only          Run only VAD validation tests
    --interruption-only Run only interruption tests
    --e2e-only          Run only end-to-end tests
    --quick             Run quick subset of tests
    --verbose, -v       Verbose output
    --html              Generate HTML report
"""

import sys
import os
import argparse
from pathlib import Path
import subprocess

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
project_root = (SCRIPT_DIR / "..").resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))


class Colors:
    """ANSI color codes."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_section(text):
    """Print formatted section."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-'*len(text)}{Colors.ENDC}")


def run_pytest(test_path, extra_args=None):
    """Run pytest on specified path."""
    args = ["pytest", str(test_path), "-v"]

    if extra_args:
        args.extend(extra_args)

    print(f"{Colors.OKCYAN}Running: {' '.join(args)}{Colors.ENDC}\n")

    result = subprocess.run(args, cwd=project_root)
    return result.returncode == 0


def check_audio_samples():
    """Check if audio samples are available."""
    audio_dir = project_root / "tests" / "voice_samples" / "wav"

    if not audio_dir.exists():
        print(f"{Colors.WARNING}⚠ Warning: Audio samples directory not found at {audio_dir}{Colors.ENDC}")
        return False

    wav_files = list(audio_dir.glob("*.wav"))
    if not wav_files:
        print(f"{Colors.WARNING}⚠ Warning: No WAV files found in {audio_dir}{Colors.ENDC}")
        return False

    print(f"{Colors.OKGREEN}✓ Found {len(wav_files)} audio samples{Colors.ENDC}")
    return True


def check_dependencies():
    """Check required dependencies."""
    print_section("Checking Dependencies")

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "numpy",
        "webrtcvad",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"{Colors.OKGREEN}✓ {package}{Colors.ENDC}")
        except ImportError:
            print(f"{Colors.FAIL}✗ {package}{Colors.ENDC}")
            missing.append(package)

    if missing:
        print(f"\n{Colors.FAIL}Missing packages: {', '.join(missing)}{Colors.ENDC}")
        print(f"Install with: uv pip install {' '.join(missing)}")
        return False

    return True


def run_vad_tests(args):
    """Run VAD validation tests."""
    print_section("Running VAD Validation Tests")

    test_file = project_root / "tests" / "backend" / "local" / "core" / "test_vad_validation.py"

    if not test_file.exists():
        print(f"{Colors.FAIL}✗ Test file not found: {test_file}{Colors.ENDC}")
        return False

    extra_args = []
    if args.verbose:
        extra_args.append("-s")
    if args.html:
        extra_args.extend(["--html=reports/vad_tests.html", "--self-contained-html"])

    return run_pytest(test_file, extra_args)


def run_interruption_tests(args):
    """Run interruption flow tests."""
    print_section("Running Interruption Flow Tests")

    test_file = project_root / "tests" / "backend" / "local" / "core" / "test_interruption_flow.py"

    if not test_file.exists():
        print(f"{Colors.FAIL}✗ Test file not found: {test_file}{Colors.ENDC}")
        return False

    extra_args = []
    if args.verbose:
        extra_args.append("-s")
    if args.html:
        extra_args.extend(["--html=reports/interruption_tests.html", "--self-contained-html"])

    return run_pytest(test_file, extra_args)


def run_e2e_tests(args):
    """Run end-to-end integration tests."""
    print_section("Running End-to-End Integration Tests")

    test_file = project_root / "tests" / "integration" / "test_e2e_vad_interruption.py"

    if not test_file.exists():
        print(f"{Colors.FAIL}✗ Test file not found: {test_file}{Colors.ENDC}")
        return False

    extra_args = []
    if args.verbose:
        extra_args.append("-s")
    if args.html:
        extra_args.extend(["--html=reports/e2e_tests.html", "--self-contained-html"])

    return run_pytest(test_file, extra_args)


def run_quick_tests(args):
    """Run quick subset of tests."""
    print_section("Running Quick Test Suite")

    # Run specific quick tests
    test_files = [
        "tests/backend/local/core/test_vad_validation.py::TestVADValidation::test_audio_samples_exist",
        "tests/backend/local/core/test_vad_validation.py::TestVADValidation::test_speech_ratio_threshold_3_percent",
        "tests/backend/local/core/test_interruption_flow.py::TestInterruptionFlow::test_interrupt_signal_handling",
    ]

    extra_args = []
    if args.verbose:
        extra_args.append("-s")

    all_passed = True
    for test_file in test_files:
        test_path = project_root / test_file.split("::")[0]
        if test_path.exists():
            if not run_pytest(test_file, extra_args):
                all_passed = False

    return all_passed


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Automated VAD and Interruption Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python tests/run_vad_tests.py

  # Run only VAD tests with verbose output
  python tests/run_vad_tests.py --vad-only -v

  # Run quick tests
  python tests/run_vad_tests.py --quick

  # Generate HTML report
  python tests/run_vad_tests.py --html
        """
    )

    parser.add_argument("--vad-only", action="store_true", help="Run only VAD validation tests")
    parser.add_argument("--interruption-only", action="store_true", help="Run only interruption tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only end-to-end tests")
    parser.add_argument("--quick", action="store_true", help="Run quick subset of tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")

    args = parser.parse_args()

    print_header("VAD and Interruption Test Suite")

    # Create reports directory if needed
    if args.html:
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        print(f"{Colors.OKCYAN}Reports will be saved to: {reports_dir}{Colors.ENDC}\n")

    # Check dependencies
    if not check_dependencies():
        print(f"\n{Colors.FAIL}✗ Dependency check failed{Colors.ENDC}")
        return 1

    # Check audio samples
    has_audio = check_audio_samples()
    if not has_audio:
        print(f"{Colors.WARNING}⚠ Some tests may be skipped due to missing audio samples{Colors.ENDC}")

    results = {}

    # Run tests based on arguments
    if args.quick:
        results["quick"] = run_quick_tests(args)
    elif args.vad_only:
        results["vad"] = run_vad_tests(args)
    elif args.interruption_only:
        results["interruption"] = run_interruption_tests(args)
    elif args.e2e_only:
        results["e2e"] = run_e2e_tests(args)
    else:
        # Run all tests
        results["vad"] = run_vad_tests(args)
        results["interruption"] = run_interruption_tests(args)
        results["e2e"] = run_e2e_tests(args)

    # Print summary
    print_header("Test Summary")

    all_passed = True
    for test_name, passed in results.items():
        status = f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC}" if passed else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
        print(f"{test_name.upper():20s}: {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print(f"{Colors.OKGREEN}{Colors.BOLD}All tests passed! 🎉{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}Some tests failed{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())