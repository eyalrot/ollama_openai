#!/usr/bin/env python3
"""
Main test runner for Ollama SDK compatibility tests.
"""
import sys
import os
import argparse
import logging
import subprocess
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOG_LEVEL, LOG_FORMAT, PROXY_HOST


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else getattr(logging, LOG_LEVEL)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_proxy_connection() -> bool:
    """Check if the proxy server is accessible."""
    import httpx
    
    try:
        # Try to connect to the proxy
        response = httpx.get(f"{PROXY_HOST}/", timeout=5)
        logging.info(f"✓ Proxy server is accessible at {PROXY_HOST}")
        return True
    except Exception as e:
        logging.error(f"✗ Cannot connect to proxy at {PROXY_HOST}: {e}")
        return False


def install_dependencies():
    """Install test dependencies."""
    logging.info("Installing test dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"✗ Failed to install dependencies: {e}")
        logging.error(f"Error output: {e.stderr}")
        sys.exit(1)


def run_pytest(
    test_files: Optional[List[str]] = None,
    markers: Optional[str] = None,
    verbose: bool = False,
    failfast: bool = False,
    coverage: bool = False
) -> int:
    """
    Run pytest with specified options.
    
    Args:
        test_files: Specific test files to run
        markers: Pytest markers to filter tests
        verbose: Enable verbose output
        failfast: Stop on first failure
        coverage: Enable coverage reporting
        
    Returns:
        Exit code from pytest
    """
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add options
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    if failfast:
        cmd.append("-x")
    
    if markers:
        cmd.extend(["-m", markers])
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Add test files or run all
    if test_files:
        cmd.extend(test_files)
    else:
        # Run all test files
        cmd.append(".")
    
    # Add color output
    cmd.append("--color=yes")
    
    # Show warnings
    cmd.append("-W default")
    
    # Run pytest
    logging.info(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Run Ollama SDK compatibility tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_tests.py
  
  # Run only embedding tests
  python run_tests.py test_embeddings.py
  
  # Run with verbose output
  python run_tests.py -v
  
  # Run only basic tests quickly
  python run_tests.py -m "not slow"
  
  # Run with coverage report
  python run_tests.py --coverage
  
  # Install dependencies and run
  python run_tests.py --install
        """
    )
    
    parser.add_argument(
        "tests",
        nargs="*",
        help="Specific test files to run (default: all tests)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "-m", "--markers",
        help="Run tests matching given mark expression (e.g., 'not slow')"
    )
    
    parser.add_argument(
        "-x", "--failfast",
        action="store_true",
        help="Stop on first test failure"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install dependencies before running tests"
    )
    
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Skip proxy connection check"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    logging.info("=== Ollama SDK Compatibility Test Suite ===")
    
    # Install dependencies if requested
    if args.install:
        install_dependencies()
    
    # Check proxy connection unless skipped
    if not args.no_check:
        if not check_proxy_connection():
            logging.error("\nPlease ensure the proxy server is running at:")
            logging.error(f"  {PROXY_HOST}")
            logging.error("\nYou can skip this check with --no-check")
            sys.exit(1)
    
    # Run tests
    logging.info("\nRunning tests...")
    exit_code = run_pytest(
        test_files=args.tests,
        markers=args.markers,
        verbose=args.verbose,
        failfast=args.failfast,
        coverage=args.coverage
    )
    
    # Report results
    if exit_code == 0:
        logging.info("\n✓ All tests passed!")
    else:
        logging.error(f"\n✗ Tests failed with exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())