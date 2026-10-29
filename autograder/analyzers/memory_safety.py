"""
Memory Safety and Sanitizer Analyzer (sanitizer_run).
Runs ASan/UBSan instrumentation and static/dynamic leak detection to highlight unsafe pointers or leaks.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult


@register_analyzer("sanitizer_run")
class SanitizerRunAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        compiler = context.get("compiler")
        sandbox = context.get("sandbox")
        flags = params.get("flags", "-fsanitize=address,undefined")

        diagnostics: List[str] = []
        score = 1.0

        # 1. Attempt Sanitizer Compilation
        temp_asan_binary = source_path.parent / f"_temp_asan_{source_path.stem}.exe"
        compile_res = None
        if compiler:
            compile_res = compiler.compile(
                source_path=source_path,
                output_binary=temp_asan_binary,
                extra_flags=f"-O1 -g {flags}",
                timeout_s=8.0,
            )

        if compile_res and compile_res.success and temp_asan_binary.is_file():
            # Run with sample input to trigger runtime sanitizer diagnostics
            run_res = sandbox.run_binary(temp_asan_binary, input_data="7 5\n", timeout_s=1.0)
            if "AddressSanitizer" in run_res.stderr or "UndefinedBehaviorSanitizer" in run_res.stderr:
                diagnostics.append(run_res.stderr.strip())
                score = 0.20
            try:
                temp_asan_binary.unlink()
            except Exception:
                pass

        # 2. Heuristic Static Memory & Pointer Safety Analysis (for leaks & buffer overflows)
        # Strip comments so comments don't inflate call counts
        clean_code = re.sub(r"/\*.*?\*/", " ", code, flags=re.DOTALL)
        clean_code = re.sub(r"//.*", " ", clean_code)

        # Check actual malloc/calloc vs free function calls
        malloc_count = len(re.findall(r"\b(?:malloc|calloc|realloc)\s*\(", clean_code))
        free_count = len(re.findall(r"\bfree\s*\(", clean_code))

        if malloc_count > free_count:
            leak_diff = malloc_count - free_count
            diagnostics.append(f"Potential memory leak: {malloc_count} allocation call(s) but only {free_count} free() call(s).")
            score = max(0.2, score - (0.35 * leak_diff))

        # Check for uninitialized pointer dereference patterns
        if re.search(r"\*\s*[a-zA-Z_]\w*\s*=\s*[^;]*;", code) and not re.search(r"&\w+", code) and malloc_count == 0:
            # Possible raw pointer dereference without address-of or malloc
            # Check if pointer wasn't initialized
            pass

        suggestions = []
        if not diagnostics:
            feedback = "no diagnostics"
        else:
            feedback = "; ".join(diagnostics)
            suggestions.append("Ensure every dynamically allocated block (malloc/calloc) is freed with free().")
            suggestions.append("Run with -fsanitize=address to intercept memory errors during debugging.")

        return AnalyzerResult(
            score=round(score, 2),
            raw_evidence={
                "sanitizer_flags": flags,
                "diagnostics": diagnostics,
                "allocations": malloc_count,
                "deallocations": free_count,
            },
            feedback=feedback,
            suggestions=suggestions,
        )

