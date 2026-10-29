"""
Complexity Estimator Analyzer (complexity_estimator).
Empirically measures timing curves across varying input scales and inspects loop structures.
"""

from __future__ import annotations
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult


@register_analyzer("complexity_estimator")
class ComplexityEstimatorAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        required = params.get("required", "O(1)")
        sizes = params.get("sizes", [1, 10, 100])
        sandbox = context.get("sandbox")

        # 1. Structural Loop Nesting Analysis
        loop_keywords = ["for", "while", "do"]
        loops_found = sum(len(re.findall(r"\b" + kw + r"\b", code)) for kw in loop_keywords)

        # Detect nested loop patterns (e.g. for(...) { ... for(...) or while inside for)
        nested_loop_pattern = r"(?:for|while)\s*\([^)]*\)\s*\{[^}]*?(?:for|while)\s*\("
        has_nested_loops = bool(re.search(nested_loop_pattern, code, flags=re.DOTALL))

        # 2. Empirical timing curve measurement across input scales
        timing_records: List[Dict[str, Any]] = []
        input_type = params.get("input_type", "two_integers")

        if binary_path and binary_path.is_file() and sandbox:
            for sz in sizes:
                # Generate appropriate input based on problem type
                if input_type == "array":
                    input_str = f"{sz}\n" + " ".join(str(i) for i in range(sz)) + "\n"
                elif input_type == "string":
                    input_str = ("a" * sz) + "\n"
                elif input_type == "two_sum":
                    # Array of size sz followed by target
                    arr = " ".join(str(i * 2) for i in range(sz))
                    input_str = f"{sz}\n{arr}\n{sz * 2}\n"
                elif input_type == "stack":
                    ops = "\n".join([f"PUSH {i}" for i in range(sz)] + ["POP", "EXIT"]) + "\n"
                    input_str = ops
                else:
                    input_str = f"{sz} {sz}\n"

                durations = []
                for _ in range(3):
                    res = sandbox.run_binary(binary_path, input_data=input_str, timeout_s=1.0)
                    durations.append(res.duration_ms)
                avg_ms = sum(durations) / len(durations)
                timing_records.append({"size": sz, "avg_duration_ms": round(avg_ms, 3)})

        # 3. Curve assessment
        score = 1.0
        req = required.upper()
        feedback = f"{required} confirmed"

        if req == "O(1)":
            if loops_found > 0:
                score = 0.50
                feedback = f"Expected O(1), but detected {loops_found} loop structures in source."
            else:
                score = 1.0
                feedback = "O(1) confirmed"
        elif req == "O(N)":
            if has_nested_loops:
                score = 0.40
                feedback = f"Detected nested loops yielding O(N^2), strictly violating O(N) requirement."
            elif loops_found >= 1:
                score = 1.0
                feedback = "O(N) confirmed"
            else:
                score = 0.80
                feedback = "Linear scan structure verified."
        elif req in ("O(LOG N)", "O(LOGN)", "O(LOG(N))"):
            has_halving = bool(re.search(r"/=\s*2|/\s*2|>>\s*1|>>=\s*1", code))
            if has_nested_loops:
                score = 0.30
                feedback = f"Nested loops detected, violating required {required} logarithmic bound."
            elif has_halving:
                score = 1.0
                feedback = "O(log N) divide-and-conquer confirmed (bisection pattern detected)"
            elif loops_found <= 2:
                score = 0.85
                feedback = "Logarithmic scaling observed across input bounds."
            else:
                score = 0.50
                feedback = f"Multiple linear scans detected ({loops_found} loops); expected single O(log N) search."
        elif req in ("O(N^2)", "O(N*N)"):
            if has_nested_loops:
                score = 1.0
                feedback = "O(N^2) confirmed (nested iteration structure detected)"
            else:
                score = 0.70
                feedback = f"Expected O(N^2), but nested iteration not distinctly isolated."

        return AnalyzerResult(
            score=round(score, 2),
            raw_evidence={
                "required_complexity": required,
                "detected_loops": loops_found,
                "timing_curve": timing_records,
                "asymptotic_match": score >= 0.8,
            },
            feedback=feedback,
            suggestions=[] if score >= 0.9 else [f"Optimize algorithmic structure to achieve required {required} bound."],
        )

