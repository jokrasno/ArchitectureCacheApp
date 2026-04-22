#!/usr/bin/env python
"""Run the test suite. Usage: python run_tests.py"""

import sys
import subprocess

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=sys.path[0] or ".",
    )
    sys.exit(result.returncode)
