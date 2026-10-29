"""
Modularity Analyzer (function_split).
Evaluates code decomposition into helper functions and separation of concerns.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult


@register_analyzer("function_split")
class FunctionSplitAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        expect_helpers = params.get("expect_helpers", True)
        min_functions = params.get("min_functions", 2)

        # Regex to find C function definitions: return_type func_name(params) {
        # Avoid control structures like if/for/while
        pattern = r"\b(?:int|void|char|float|double|long|size_t)\s+([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{"
        matches: List[str] = re.findall(pattern, code)

        # Filter out keywords if any matched accidentally
        ignore = {"if", "for", "while", "switch", "catch"}
        functions_found = [m for m in matches if m not in ignore]
        func_count = len(functions_found)

        suggestions = []
        if expect_helpers and func_count < min_functions:
            score = 0.30
            feedback = "only main(); no helper"
            suggestions.append("Extract core logic into a helper function (e.g. int add(int a, int b)) and call it from main.")
        else:
            score = 1.0
            feedback = f"{func_count} functions defined (modular helper architecture verified)"

        return AnalyzerResult(
            score=round(score, 2),
            raw_evidence={
                "functions_defined": func_count,
                "expected_min": min_functions,
                "function_names": functions_found,
            },
            feedback=feedback,
            suggestions=suggestions,
        )

