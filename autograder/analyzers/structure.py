"""
Structure and Static Analysis Analyzer (static_analysis).
Evaluates cyclomatic complexity, function length, header inclusion, and structural organization.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Any, Optional
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult

try:
    import lizard
except ImportError:
    lizard = None


@register_analyzer("static_analysis")
class StaticAnalysisAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        max_cyclomatic_allowed = params.get("max_cyclomatic", 8)
        max_length_allowed = params.get("max_function_length", 40)

        # 1. Structural checks
        has_headers = bool(re.search(r"#include\s*<[\w\.\/]+>", code))
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        total_loc = len(lines)

        # 2. Lizard complexity analysis
        max_ccn = 1
        max_func_len = total_loc
        function_metrics = []

        if lizard is not None:
            try:
                analysis = lizard.analyze_file(str(source_path))
                for func in analysis.function_list:
                    function_metrics.append({
                        "name": func.name,
                        "cyclomatic_complexity": func.cyclomatic_complexity,
                        "length": func.length,
                        "nloc": func.nloc,
                    })
                    if func.cyclomatic_complexity > max_ccn:
                        max_ccn = func.cyclomatic_complexity
                    if func.length > max_func_len:
                        max_func_len = func.length
            except Exception:
                pass
        else:
            # Fallback simple CCN estimation
            decision_keywords = ["if", "for", "while", "case", "&&", "||", "?"]
            for kw in decision_keywords:
                max_ccn += len(re.findall(r"\b" + re.escape(kw) + r"\b", code))

        # 3. Assess structure
        issues = []
        score = 1.0

        has_comments = bool(re.search(r"//|/\*", code))
        if not has_comments or not has_headers:
            issues.append("no headers" if not has_headers else "no documentation headers")
            score -= 0.20

        # Check if single-block / dense
        is_single_block = (code.count("\n\n") == 0 and not has_comments) or len(function_metrics) <= 1
        if is_single_block:
            issues.append("single-block code")
            score -= 0.20

        if max_ccn > max_cyclomatic_allowed:
            issues.append(f"cyclomatic complexity {max_ccn} > {max_cyclomatic_allowed}")
            score -= 0.20

        if max_func_len > max_length_allowed:
            issues.append(f"function length {max_func_len} > {max_length_allowed}")
            score -= 0.20

        score = max(0.2, min(1.0, score))

        if not issues:
            feedback = f"Clean structure (CCN {max_ccn}, max len {max_func_len} LOC)."
        else:
            feedback = ", ".join(issues)

        suggestions = []
        if not has_headers:
            suggestions.append("Include standard library headers explicitly (e.g. #include <stdio.h>).")
        if is_single_block:
            suggestions.append("Break logic into distinct visual sections and functions rather than a single monolithic block.")
        if max_ccn > max_cyclomatic_allowed:
            suggestions.append(f"Reduce branching complexity (current cyclomatic complexity is {max_ccn}).")

        return AnalyzerResult(
            score=round(score, 2),
            raw_evidence={
                "has_headers": has_headers,
                "max_cyclomatic": max_ccn,
                "max_function_length": max_func_len,
                "total_loc": total_loc,
                "functions": function_metrics,
            },
            feedback=feedback,
            suggestions=suggestions,
        )
