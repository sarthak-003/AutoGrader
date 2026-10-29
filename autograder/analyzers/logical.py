"""
Logical Edge Case Analyzer (edge_case_runner).
Specifically probes extreme boundary inputs, zero handling, signed overflow, and underflow.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult
from autograder.counter_test_generator import CounterTestGenerator


@register_analyzer("edge_case_runner")
class EdgeCaseRunnerAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        if not binary_path or not binary_path.is_file():
            return AnalyzerResult(
                score=0.0,
                raw_evidence={"error": "Binary missing"},
                feedback="Cannot evaluate edge cases: compiled binary missing.",
            )

        cases_to_test = params.get("cases", ["negatives", "zero", "int_overflow"])
        custom_cases = params.get("custom_cases", [])
        sandbox = context.get("sandbox")
        time_limit = context.get("time_limit_s", 1.0)
        mem_limit = context.get("memory_limit_mb", 64)

        test_suite: List[tuple[str, str, str]] = []

        # 1. Custom rule-driven cases defined by instructor
        if custom_cases:
            for c in custom_cases:
                inp = c.get("input", "")
                if not inp.endswith("\n"):
                    inp += "\n"
                exp = str(c.get("expected", "")).strip()
                lbl = c.get("label", "custom edge case")
                test_suite.append((inp, exp, lbl))

        # 2. Built-in presets for numerical / boundary problems
        else:
            if "zero" in cases_to_test:
                test_suite.append(("0 0\n", "0", "zero addition"))
                test_suite.append(("0 42\n", "42", "zero with positive"))
            if "negatives" in cases_to_test:
                test_suite.append(("-10 -20\n", "-30", "negative addition"))
                test_suite.append(("50 -20\n", "30", "mixed signs"))
            if "int_overflow" in cases_to_test:
                test_suite.append(("2147483647 1\n", "2147483648", "INT_MAX + 1 overflow"))
                test_suite.append(("-2147483648 -1\n", "-2147483649", "INT_MIN - 1 underflow"))

        total = len(test_suite)
        passed = 0
        overflow_failed = False
        failures: List[Dict[str, Any]] = []

        for inp, expected, label in test_suite:
            res = sandbox.run_binary(
                binary_path,
                input_data=inp,
                timeout_s=time_limit,
                memory_limit_mb=mem_limit,
            )
            out_clean = res.stdout.strip()
            # If expected is 2147483648, 32-bit signed int wraps to -2147483648
            if "overflow" in label or "underflow" in label:
                if out_clean != expected:
                    overflow_failed = True
                    failures.append({
                        "case": label,
                        "input": inp.strip(),
                        "expected": expected,
                        "got": out_clean,
                        "note": "signed integer overflow",
                    })
                    continue

            # Two-Sum multi-solution alternative pair check
            if "two_sum" in context.get("problem", "") or params.get("checker") == "two_sum":
                lines = [l.strip() for l in inp.strip().splitlines() if l.strip()]
                if len(lines) >= 3 and expected != "-1":
                    try:
                        arr = [int(x) for x in lines[1].split()]
                        tgt = int(lines[2])
                        toks = out_clean.split()
                        if len(toks) == 2:
                            ci, cj = int(toks[0]), int(toks[1])
                            if 0 <= ci < len(arr) and 0 <= cj < len(arr) and ci != cj and arr[ci] + arr[cj] == tgt:
                                passed += 1
                                continue
                    except Exception:
                        pass

            if out_clean == expected:
                passed += 1
            else:
                failures.append({
                    "case": label,
                    "input": inp.strip(),
                    "expected": expected,
                    "got": out_clean,
                    "note": f"Incorrect result for {label}",
                })

        suggestions = []
        if overflow_failed:
            score = 0.80  # 8/10 as in example
            feedback = "overflow on INT_MAX+1 not handled"
            suggestions.append("Handle overflow explicitly with a wider integer type (e.g. long long) or bounds check b <= INT_MAX - a.")
        elif failures:
            score = max(0.0, round(passed / total, 2))
            feedback = f"Failed {len(failures)} edge cases: {failures[0]['case']}"
            suggestions.append(f"Review boundary handling for: {failures[0]['case']}")
        else:
            score = 1.0
            feedback = "All boundary edge cases (zeros, negatives, extreme values) passed cleanly."

        return AnalyzerResult(
            score=score,
            raw_evidence={
                "cases_evaluated": cases_to_test,
                "total_probes": total,
                "failures": failures,
                "overflow_handled": not overflow_failed,
            },
            feedback=feedback,
            failing_cases=failures,
            suggestions=suggestions,
        )

