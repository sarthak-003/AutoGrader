"""
Syntax and Compiler Warnings Analyzer (compiler_warnings).
Evaluates adherence to compilation standards and flags unused variables, type issues, etc.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult


@register_analyzer("compiler_warnings")
class CompilerWarningsAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        compiler = context.get("compiler")
        if not compiler:
            return AnalyzerResult(
                score=1.0,
                raw_evidence={"note": "Compiler not found in context"},
                feedback="No compiler available for warning analysis.",
            )

        flags = params.get("flags", "-Wall -Wextra -std=c11")
        # Strip -Werror for warning count analysis so we see all warnings, include -O2 for attribute checking
        analysis_flags = flags.replace("-Werror", "").strip()
        if "-O2" not in analysis_flags and "-O1" not in analysis_flags:
            analysis_flags = f"-O2 {analysis_flags}"
        if "-D__USE_MINGW_ANSI_STDIO=1" not in analysis_flags and os.name == "nt":
            analysis_flags = f"{analysis_flags} -D__USE_MINGW_ANSI_STDIO=1"

        temp_out = source_path.parent / f"_temp_syntax_{source_path.stem}.exe"
        compile_res = compiler.compile(
            source_path=source_path,
            output_binary=temp_out,
            extra_flags=analysis_flags,
            timeout_s=15.0,
        )

        try:
            if temp_out.is_file():
                temp_out.unlink()
        except Exception:
            pass

        warnings = list(compile_res.warnings)

        # For toolchains where warn_unused_result or strict prototypes are disabled by default,
        # inspect for unchecked I/O return values (e.g. scanf without checking return code)
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        if re.search(r"\bscanf\s*\(", code) and not re.search(r"if\s*\(\s*scanf|while\s*\(\s*scanf|[a-zA-Z_]\w*\s*=\s*scanf", code):
            if not any("-Wunused" in w for w in warnings):
                warnings.append("warning: ignoring return value of 'scanf' [-Wunused-result]")

        warning_count = len(warnings)

        if not compile_res.success and warning_count == 0:
            return AnalyzerResult(
                score=0.0,
                raw_evidence={"errors": compile_res.stderr.splitlines(), "warnings": []},
                feedback="Compilation failed due to fatal syntax errors.",
                suggestions=["Resolve syntax and typing errors before resubmitting."],
            )

        # Base scoring: 1.0 for 0 warnings, -0.10 per warning down to minimum 0.0
        score = max(0.0, 1.0 - (0.10 * warning_count))

        # Categorize warning types (e.g. -Wunused-parameter)
        warning_types = []
        for w in warnings:
            match = re.search(r"\[-W([\w\-]+)\]", w)
            if match:
                warning_types.append(f"-W{match.group(1)}")
            else:
                warning_types.append("warning")

        if warning_count == 0:
            feedback = "Clean compilation with zero warnings."
        elif warning_count == 1:
            feedback = f"one {warning_types[0]} warning"
        else:
            types_str = ", ".join(set(warning_types))
            feedback = f"{warning_count} warnings detected ({types_str})"

        return AnalyzerResult(
            score=round(score, 2),
            raw_evidence={
                "warning_count": warning_count,
                "warnings": warnings,
                "flags_used": analysis_flags,
            },
            feedback=feedback,
            suggestions=[f"Fix compiler diagnostic: {w}" for w in warnings[:3]],
        )
