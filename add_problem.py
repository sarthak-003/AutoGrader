#!/usr/bin/env python3
"""
Interactive & Scriptable Problem & Rule Builder for AutoGrader.
Enables instructors and developers to easily create a new problem rule set
and hidden test cases with full validation.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
RULES_DIR = BASE_DIR / "rules"
TESTS_DIR = BASE_DIR / "tests"


def create_problem(
    problem_name: str,
    time_limit_s: float = 2.0,
    memory_limit_mb: int = 64,
    complexity: str = "O(N)",
    min_functions: int = 2,
    max_cyclomatic: int = 6,
    test_cases: list[tuple[str, str]] | None = None,
) -> Path:
    clean_name = re.sub(r"[^a-z0-9_]", "_", problem_name.strip().lower()).strip("_")
    if not clean_name:
        raise ValueError("Invalid problem name. Must contain alphanumeric characters.")

    # 1. Setup tests directory
    prob_tests_dir = TESTS_DIR / clean_name
    prob_tests_dir.mkdir(parents=True, exist_ok=True)

    if not test_cases:
        # Default sample tests if none provided
        test_cases = [
            ("5\n1 2 3 4 5\n", "15\n"),
            ("1\n42\n", "42\n"),
            ("3\n-5 0 5\n", "0\n"),
        ]

    for idx, (inp, out) in enumerate(test_cases, 1):
        in_file = prob_tests_dir / f"test_{idx:02d}.in"
        out_file = prob_tests_dir / f"test_{idx:02d}.out"
        with open(in_file, "w", encoding="utf-8") as f:
            f.write(inp if inp.endswith("\n") else inp + "\n")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(out_content if (out_content := out.strip()) else "")
            f.write("\n")

    # 2. Setup rule specification JSON
    rule_spec = {
        "problem": clean_name,
        "time_limit_s": time_limit_s,
        "memory_limit_mb": memory_limit_mb,
        "metrics": [
            {
                "name": "correctness",
                "analyzer": "io_tests",
                "weight": 0.25,
                "params": {"testset_dir": f"tests/{clean_name}/"},
            },
            {
                "name": "complexity",
                "analyzer": "complexity_estimator",
                "weight": 0.20,
                "params": {"required": complexity, "input_type": "array", "sizes": [10, 100, 1000]},
            },
            {
                "name": "modularity",
                "analyzer": "function_split",
                "weight": 0.15,
                "params": {"expect_helpers": True, "min_functions": min_functions},
            },
            {
                "name": "syntax",
                "analyzer": "compiler_warnings",
                "weight": 0.10,
                "params": {"flags": "-Wall -Wextra -Werror -std=c11"},
            },
            {
                "name": "structure",
                "analyzer": "static_analysis",
                "weight": 0.10,
                "params": {"max_cyclomatic": max_cyclomatic, "max_function_length": 40},
            },
            {
                "name": "logical",
                "analyzer": "edge_case_runner",
                "weight": 0.10,
                "params": {
                    "custom_cases": [
                        {"input": "1\n0\n", "expected": "0", "label": "Zero boundary condition"},
                        {"input": "2\n-10 -20\n", "expected": "-30", "label": "Negative values boundary"},
                    ]
                },
            },
            {
                "name": "readability",
                "analyzer": "llm_review",
                "weight": 0.10,
                "params": {
                    "model": "llama-3.3-70b-versatile",
                    "use_ollama": False,
                    "ollama_model": "llama3",
                    "temperature": 0,
                    "seed": 42,
                },
            },
        ],
    }

    rule_path = RULES_DIR / f"{clean_name}.json"
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    with open(rule_path, "w", encoding="utf-8") as f:
        json.dump(rule_spec, f, indent=2)

    return rule_path


def main():
    parser = argparse.ArgumentParser(description="Create new problem rules and test cases for AutoGrader.")
    parser.add_argument("--name", "-n", type=str, help="Problem identifier (e.g. fibonacci, reverse_string)")
    parser.add_argument("--time-limit", "-t", type=float, default=2.0, help="Time limit in seconds per test (default: 2.0)")
    parser.add_argument("--memory-limit", "-m", type=int, default=64, help="Memory limit in MB (default: 64)")
    parser.add_argument("--complexity", "-c", type=str, default="O(N)", help="Target asymptotic complexity (e.g. O(1), O(N), O(log N), O(N^2))")
    parser.add_argument("--min-functions", "-f", type=int, default=2, help="Minimum modular functions required (default: 2)")

    args = parser.parse_args()

    name = args.name
    if not name:
        print("=== AutoGrader Problem & Rule Creator Wizard ===")
        name = input("Enter problem name (e.g. matrix_transpose, reverse_string): ").strip()
        if not name:
            print("Problem name cannot be empty.", file=sys.stderr)
            sys.exit(1)

    rule_path = create_problem(
        problem_name=name,
        time_limit_s=args.time_limit,
        memory_limit_mb=args.memory_limit,
        complexity=args.complexity,
        min_functions=args.min_functions,
    )

    clean_name = rule_path.stem
    print(f"\n[+] Successfully created rule specification: {rule_path}")
    print(f"[+] Test directory created at: tests/{clean_name}/")
    print(f"\nNext steps:")
    print(f"1. Add your custom test cases in tests/{clean_name}/ (e.g. test_01.in and test_01.out)")
    print(f"2. Run evaluation with:")
    print(f"   python run_grader.py --submission submissions/your_solution.c --rules rules/{clean_name}.json")
    print(f"3. Or open the Web UI at http://127.0.0.1:5000 and select '{clean_name}.json' from the dropdown!\n")


if __name__ == "__main__":
    main()

