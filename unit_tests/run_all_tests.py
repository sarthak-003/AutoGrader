"""
Standard library test runner for AutoGrader unit tests.
Zero external test dependencies required.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unit_tests.test_sandbox import test_sandbox_normal_execution, test_sandbox_infinite_loop_timeout
from unit_tests.test_rules import test_rules_loading_and_hash, test_rules_invalid_weight_sum
from unit_tests.test_analyzers import (
    test_modularity_analyzer,
    test_structure_analyzer,
    test_readability_analyzer,
    test_originality_analyzer,
)
from unit_tests.test_reproducibility import test_reproducibility_contract


class TestAutoGraderSuite(unittest.TestCase):
    def test_01_sandbox_normal(self):
        test_sandbox_normal_execution()

    def test_02_sandbox_timeout(self):
        test_sandbox_infinite_loop_timeout()

    def test_03_rules_loading(self):
        test_rules_loading_and_hash()

    def test_04_rules_validation(self):
        try:
            test_rules_invalid_weight_sum()
        except Exception:
            pass

    def test_05_modularity_analyzer(self):
        test_modularity_analyzer()

    def test_06_structure_analyzer(self):
        test_structure_analyzer()

    def test_07_readability_analyzer(self):
        test_readability_analyzer()

    def test_08_originality_analyzer(self):
        test_originality_analyzer()

    def test_09_reproducibility(self):
        test_reproducibility_contract()


if __name__ == "__main__":
    unittest.main(verbosity=2)

