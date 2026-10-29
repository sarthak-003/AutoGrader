#!/usr/bin/env python3
"""
Regenerate benchmark reports for all sample submissions.
"""
from pathlib import Path
from autograder.config import GradingRules
from autograder.coordinator import GradingCoordinator

def main():
    c = GradingCoordinator()
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    benchmarks = [
        ("rules/add_two_integers.json", "submissions/add_student.c"),
        ("rules/add_two_integers.json", "submissions/add_perfect.c"),
        ("rules/add_two_integers.json", "submissions/add_infinite_loop.c"),
        ("rules/add_two_integers.json", "submissions/add_crash_segfault.c"),
        ("rules/add_two_integers.json", "submissions/add_memory_leak.c"),
        ("rules/add_two_integers.json", "submissions/add_compile_error.c"),
        ("rules/add_with_plagiarism_check.json", "submissions/add_plagiarized.c"),
        ("rules/two_sum_sorted.json", "submissions/two_sum_quadratic.c"),
        ("rules/two_sum_sorted.json", "submissions/two_sum_optimal.c"),
        ("rules/dynamic_stack.json", "submissions/stack_leaky.c"),
        ("rules/dynamic_stack.json", "submissions/stack_robust.c"),
        ("rules/palindrome_checker.json", "submissions/palindrome_buggy.c"),
        ("rules/palindrome_checker.json", "submissions/palindrome_perfect.c"),
        ("rules/binary_search.json", "submissions/binary_search_linear.c"),
        ("rules/binary_search.json", "submissions/binary_search_optimal.c"),
    ]

    print("[*] Regenerating reports across all problem suites...")
    for r_path, s_path in benchmarks:
        rules = GradingRules.load_from_file(r_path)
        res = c.evaluate(Path(s_path), rules, reports_dir=reports_dir)
        grade = res["grade"]
        print(f" -> {s_path:<36} [{rules.problem:<20}] Grade: {grade:5.1f}/100")

    print("[+] All reports regenerated successfully in reports/")

if __name__ == "__main__":
    main()

