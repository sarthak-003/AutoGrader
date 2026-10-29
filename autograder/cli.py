"""
AutoGrader Command Line Interface.
Supports single-file unattended evaluation or batch class grading.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from autograder.config import GradingRules
from autograder.coordinator import GradingCoordinator
from autograder.compiler import CCompiler


def main():
    parser = argparse.ArgumentParser(
        description="AutoGrader: A Rule-Driven Evaluator for C Programs"
    )
    parser.add_argument(
        "--submission",
        "-s",
        type=str,
        help="Path to student C submission file (.c)",
    )
    parser.add_argument(
        "--submissions-dir",
        "-d",
        type=str,
        help="Path to directory containing multiple student submissions",
    )
    parser.add_argument(
        "--rules",
        "-r",
        type=str,
        required=True,
        help="Path to external rules JSON file",
    )
    parser.add_argument(
        "--reports-dir",
        "-o",
        type=str,
        default="reports",
        help="Directory where JSON and TXT reports will be written (default: reports)",
    )
    parser.add_argument(
        "--compiler",
        type=str,
        default=None,
        help="Explicit path to gcc/clang executable",
    )

    args = parser.parse_args()

    # Load rules
    try:
        rules = GradingRules.load_from_file(args.rules)
    except Exception as e:
        print(f"Error loading rules from {args.rules}: {e}", file=sys.stderr)
        sys.exit(1)

    compiler = CCompiler(args.compiler)
    coordinator = GradingCoordinator(compiler=compiler)

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    if args.submission:
        sub_path = Path(args.submission)
        if not sub_path.is_file():
            print(f"Submission not found: {sub_path}", file=sys.stderr)
            sys.exit(1)

        print(f"[*] Evaluating {sub_path.name} against rules: {rules.problem}...")
        report = coordinator.evaluate(sub_path, rules, reports_dir=reports_dir)
        grade = report["grade"]
        print(f"[+] Grading complete for {sub_path.name}: Grade = {grade:.1f}/100")
        txt_path = reports_dir / f"{sub_path.stem}.txt"
        print(f"[+] Text report written to: {txt_path}")
        json_path = reports_dir / f"{sub_path.stem}.json"
        print(f"[+] JSON report written to: {json_path}")

    elif args.submissions_dir:
        sub_dir = Path(args.submissions_dir)
        if not sub_dir.is_dir():
            print(f"Directory not found: {sub_dir}", file=sys.stderr)
            sys.exit(1)

        c_files = sorted(list(sub_dir.glob("*.c")))
        if not c_files:
            print(f"No .c files found in {sub_dir}", file=sys.stderr)
            sys.exit(1)

        print(f"[*] Found {len(c_files)} submissions in {sub_dir}. Starting batch evaluation...")
        for c_file in c_files:
            try:
                report = coordinator.evaluate(c_file, rules, reports_dir=reports_dir)
                grade = report["grade"]
                print(f" -> {c_file.name:<25} Grade: {grade:5.1f}/100 | First pass: compiled={report['first_pass']['compiled']} smoke={report['first_pass']['smoke_ok']}")
            except Exception as e:
                print(f" -> {c_file.name:<25} ERROR: {e}")

        print(f"[+] Batch grading complete. All reports saved to: {reports_dir}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

