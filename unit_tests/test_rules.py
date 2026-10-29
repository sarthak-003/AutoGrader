"""
Unit tests for external rules parsing, validation, and hash generation.
"""

import json
import tempfile
from pathlib import Path
from autograder.config import GradingRules


def test_rules_loading_and_hash():
    rules_dict = {
        "problem": "test_problem",
        "time_limit_s": 2,
        "memory_limit_mb": 128,
        "metrics": [
            {"name": "m1", "analyzer": "io_tests", "weight": 0.60, "params": {}},
            {"name": "m2", "analyzer": "static_analysis", "weight": 0.40, "params": {}},
        ]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(rules_dict, f)
        rule_path = f.name

    rules = GradingRules.load_from_file(rule_path)
    assert rules.problem == "test_problem"
    assert rules.time_limit_s == 2.0
    assert rules.memory_limit_mb == 128
    assert len(rules.metrics) == 2
    assert rules.rules_hash.startswith("sha256:")


def test_rules_invalid_weight_sum():
    invalid_dict = {
        "problem": "invalid_weights",
        "metrics": [
            {"name": "m1", "analyzer": "io_tests", "weight": 0.50},
            {"name": "m2", "analyzer": "static_analysis", "weight": 0.30},
        ]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(invalid_dict, f)
        rule_path = f.name

    with pytest.raises(ValueError) as exc:
        GradingRules.load_from_file(rule_path)
    assert "Metric weights must sum to 1.00" in str(exc.value)
