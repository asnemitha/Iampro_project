"""
Standalone Runner for CiteGuard API Robustness and Metadata Drift Tests.

Executes all 13 test scenarios in test_api_robustness.py, gathers telemetry,
and prints structured execution metrics.
"""

import sys
import time
import unittest
from pathlib import Path

# Add backend and test directory to path
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_api_robustness import TestAPIRobustnessAndMetadataDrift


def run_tests():
    print("=" * 75)
    print("CITEGUARD API ROBUSTNESS & FAULT-INJECTION TEST RUNNER")
    print("=" * 75)
    print(f"Python Version : {sys.version.split()[0]}")
    print(f"Test Directory : {TEST_DIR}")
    print(f"Target Module  : test_api_robustness.py")
    print("=" * 75)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIRobustnessAndMetadataDrift)
    start_time = time.time()

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed = time.time() - start_time

    print("\n" + "=" * 75)
    print("EXECUTION SUMMARY")
    print("=" * 75)
    print(f"Total Tests Run : {result.testsRun}")
    print(f"Successes       : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures        : {len(result.failures)}")
    print(f"Errors          : {len(result.errors)}")
    print(f"Elapsed Time    : {elapsed:.3f}s")
    print("=" * 75)

    if result.wasSuccessful():
        print(f"[SUCCESS] All {result.testsRun} robustness and fault-injection scenarios passed successfully.")
        return 0
    else:
        print("[FAILURE] Robustness test suite encountered failures or errors.")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
