"""
Agent Coordinator and Orchestrator.
Performs initial sanity sweeps, dispatches expert analyzers concurrently,
and collates all evidence into final reproducible reports.
"""

from __future__ import annotations
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, Optional, List

from autograder.config import GradingRules, FirstPassResult, AnalyzerResult
from autograder.compiler import CCompiler
from autograder.sandbox import ProcessSandbox
from autograder.analyzers.base import get_analyzer
from autograder.reporter import Reporter


class GradingCoordinator:
    """Intelligent coordinator orchestrating rule-driven grading sweeps and analysis."""

    def __init__(
        self,
        compiler: Optional[CCompiler] = None,
        sandbox: Optional[ProcessSandbox] = None,
    ):
        self.compiler = compiler or CCompiler()
        self.sandbox = sandbox or ProcessSandbox()

    def run_first_pass(
        self,
        source_path: Path,
        temp_binary_path: Path,
        rules: GradingRules,
    ) -> FirstPassResult:
        """Executes a cheap sanity sweep prior to expert analyzer dispatch."""
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        # 1. Static Sanity
        has_main = bool(re.search(r"\bmain\s*\(", code))
        has_reader = bool(re.search(r"\b(?:scanf|getchar|fgets|fread|read)\b", code))
        has_writer = bool(re.search(r"\b(?:printf|puts|putchar|fwrite|write)\b", code))
        has_return = bool(re.search(r"\breturn\b", code))
        static_ok = has_main and has_reader and has_writer and has_return

        # 2. Compile Check
        compile_res = self.compiler.compile(
            source_path=source_path,
            output_binary=temp_binary_path,
            extra_flags="-O2 -Wall -Wextra -std=c11",
            timeout_s=15.0,
        )

        compiled = compile_res.success and temp_binary_path.is_file()
        smoke_ok = False
        suspected_infinite_loop = False

        # 3. Smoke Run
        if compiled:
            sample_input = "7 5\n"
            smoke_res = self.sandbox.run_binary(
                temp_binary_path,
                input_data=sample_input,
                timeout_s=rules.time_limit_s,
                memory_limit_mb=rules.memory_limit_mb,
            )
            if smoke_res.timed_out:
                suspected_infinite_loop = True
                smoke_ok = False
            elif smoke_res.crashed or smoke_res.memory_exceeded:
                smoke_ok = False
            else:
                smoke_ok = True

        return FirstPassResult(
            compiled=compiled,
            smoke_ok=smoke_ok,
            suspected_infinite_loop=suspected_infinite_loop,
            static_sanity_ok=static_ok,
            details={
                "has_main": has_main,
                "has_reader": has_reader,
                "has_writer": has_writer,
                "has_return": has_return,
                "compile_warnings": len(compile_res.warnings) if compile_res else 0,
            },
        )

    def evaluate(
        self,
        submission_path: str | Path,
        rules: GradingRules,
        reports_dir: Optional[str | Path] = "reports",
    ) -> Dict[str, Any]:
        """Runs the complete unattended grading pipeline for a submission."""
        src_path = Path(submission_path).resolve()
        if not src_path.is_file():
            raise FileNotFoundError(f"Submission file not found: {src_path}")

        # Shared context
        context = {
            "compiler": self.compiler,
            "sandbox": self.sandbox,
            "time_limit_s": rules.time_limit_s,
            "memory_limit_mb": rules.memory_limit_mb,
            "problem": rules.problem,
        }

        # Create temporary directory for compilation binary
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_bin = Path(tmp_dir) / f"{src_path.stem}.exe"

            # Execute First Pass
            first_pass = self.run_first_pass(src_path, temp_bin, rules)

            dynamic_analyzers = {"io_tests", "edge_case_runner", "complexity_estimator", "sanitizer_run"}
            metrics_results: List[Dict[str, Any]] = []
            collected_suggestions: List[str] = []
            flags: List[str] = []

            if first_pass.suspected_infinite_loop:
                flags.append("suspected_infinite_loop")

            # Dispatch Analyzers
            def run_single_metric(metric_rule) -> Dict[str, Any]:
                an_name = metric_rule.analyzer
                # If infinite loop or compile failed, skip dynamic execution analyzers
                if (first_pass.suspected_infinite_loop or not first_pass.compiled) and an_name in dynamic_analyzers:
                    if first_pass.suspected_infinite_loop:
                        feedback = "Skipped: suspected infinite loop in smoke run."
                    else:
                        feedback = "Skipped: compilation failed."
                    return {
                        "name": metric_rule.name,
                        "analyzer": an_name,
                        "score": 0.0,
                        "weight": metric_rule.weight,
                        "contribution": 0.0,
                        "evidence": {"skipped": True, "reason": feedback},
                        "feedback": feedback,
                        "suggestions": [],
                    }

                try:
                    analyzer = get_analyzer(an_name)
                    res = analyzer.analyze(
                        source_path=src_path,
                        binary_path=temp_bin if first_pass.compiled else None,
                        params=metric_rule.params,
                        context=context,
                    )
                    contribution = round(res.score * metric_rule.weight * 100.0, 1)
                    return {
                        "name": metric_rule.name,
                        "analyzer": an_name,
                        "score": res.score,
                        "weight": metric_rule.weight,
                        "contribution": contribution,
                        "evidence": res.raw_evidence,
                        "feedback": res.feedback,
                        "suggestions": res.suggestions,
                    }
                except Exception as e:
                    return {
                        "name": metric_rule.name,
                        "analyzer": an_name,
                        "score": 0.0,
                        "weight": metric_rule.weight,
                        "contribution": 0.0,
                        "evidence": {"error": str(e)},
                        "feedback": f"Analyzer execution error: {str(e)}",
                        "suggestions": [],
                    }

            # Parallel dispatch where possible
            with ThreadPoolExecutor(max_workers=min(4, len(rules.metrics) or 1)) as executor:
                futures = {executor.submit(run_single_metric, m): m for m in rules.metrics}
                # Preserve original ordering
                results_map = {}
                for future in as_completed(futures):
                    res_dict = future.result()
                    results_map[res_dict["name"]] = res_dict

            for m in rules.metrics:
                m_res = results_map[m.name]
                metrics_results.append(m_res)
                for s in m_res.get("suggestions", []):
                    if s not in collected_suggestions:
                        collected_suggestions.append(s)

            # Check originality flag
            for m_res in metrics_results:
                if m_res["name"] == "originality":
                    if m_res.get("evidence", {}).get("flagged"):
                        flags.append("suspected_plagiarism")

            total_grade = round(sum(m["contribution"] for m in metrics_results), 1)

            # Tool versions
            tool_versions = {
                "gcc": self.compiler.version,
                "cppcheck": "2.14.1",
                "lizard": "1.17.10",
            }

            profile = Reporter.get_problem_profile(rules.problem)

            report_data = {
                "submission": src_path.name,
                "problem": rules.problem,
                "rules_hash": rules.rules_hash,
                "grade": total_grade,
                "first_pass": {
                    "compiled": first_pass.compiled,
                    "smoke_ok": first_pass.smoke_ok,
                    "suspected_infinite_loop": first_pass.suspected_infinite_loop,
                },
                "metrics": metrics_results,
                "flags": flags,
                "suggestions": collected_suggestions,
                "deductions": [],
                "usefulness_limitations": profile,
                "tool_versions": tool_versions,
            }

            report_data["deductions"] = Reporter.compute_deductions(report_data)

            # Write reports if requested
            if reports_dir:
                rep_dir = Path(reports_dir)
                json_path = rep_dir / f"{src_path.stem}.json"
                txt_path = rep_dir / f"{src_path.stem}.txt"
                Reporter.generate_json_report(report_data, json_path)
                Reporter.generate_text_report(report_data, txt_path)

            return report_data
