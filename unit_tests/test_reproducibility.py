"""
Contract Verification: Same submission + same rules -> same grade.
Ensures deterministic grading across multiple runs.
"""

from pathlib import Path
from autograder.config import GradingRules
from autograder.coordinator import GradingCoordinator


def test_reproducibility_contract():
    rules_path = Path("rules/add_two_integers.json")
    rules = GradingRules.load_from_file(rules_path)
    submission_path = Path("submissions/add_student.c")

    coordinator = GradingCoordinator()

    # Run evaluation first time
    report_1 = coordinator.evaluate(submission_path, rules, reports_dir=None)

    # Run evaluation second time
    report_2 = coordinator.evaluate(submission_path, rules, reports_dir=None)

    # Assert exact match
    assert report_1["grade"] == report_2["grade"], "Grading must be deterministic"
    assert report_1["rules_hash"] == report_2["rules_hash"]
    
    # Assert each metric score matches
    m1 = {m["name"]: m["score"] for m in report_1["metrics"]}
    m2 = {m["name"]: m["score"] for m in report_2["metrics"]}
    assert m1 == m2, f"Metrics mismatch: {m1} vs {m2}"

