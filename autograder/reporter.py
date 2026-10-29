"""
Reporter and Result Collation Module.
Generates machine-readable JSON reports and human-readable text reports
adhering strictly to problem-specific requirements with on-point deduction analysis.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from autograder.counter_test_generator import CounterTestGenerator


class Reporter:
    """Collates evaluation metrics into machine JSON and student TXT formats."""

    PROBLEM_PROFILES = {
        "two_sum_sorted": {
            "usefulness": [
                {
                    "use_case": "Algorithmic Efficiency Screening in Quantitative & Tech Interviews",
                    "example": "Evaluates whether candidates discover the O(N) two-pointer technique on sorted arrays versus naive O(N^2) brute-force nested loops across 10,000+ elements.",
                    "benefit": "Automates algorithmic performance gating without subjective manual code reviews.",
                },
                {
                    "use_case": "Special Judge Multi-Solution Verification",
                    "example": "When an array contains multiple valid index pairs (e.g. arr[1]+arr[4]=70 and arr[2]+arr[3]=70), the agent accepts any mathematically valid pair.",
                    "benefit": "Eliminates false negatives common in rigid exact-match string diff graders.",
                },
                {
                    "use_case": "Memory Bounds & Linear Array Traversal Gating",
                    "example": "Verifies that array indexing does not produce off-by-one errors or out-of-bounds access on negative target numbers.",
                    "benefit": "Guarantees runtime index safety prior to production algorithm deployment.",
                },
            ],
            "limitations": [
                {
                    "limitation": "Multi-solution Non-determinism with Rigid Checkers",
                    "example": "If a student outputs a different valid index pair than the single reference output, strict line-by-line diffs fail unless a Special Judge is active.",
                    "mitigation": "AutoGrader includes an integrated two_sum validator that verifies arr[i] + arr[j] == target dynamically.",
                },
                {
                    "limitation": "CPU L1/L2 Cache Locality Skewing Timing Curves",
                    "example": "An O(N) linear scan on a small array fits entirely in CPU cache, showing sub-microsecond runtimes that distort empirical curve fitting.",
                    "mitigation": "Profile hardware instruction retirement counts and CPU cycles rather than raw wall-clock duration.",
                },
            ],
        },
        "dynamic_stack": {
            "usefulness": [
                {
                    "use_case": "Systems Programming & Embedded OS Kernel Call Stacks",
                    "example": "In mission-critical firmware, dynamic stack structures must strictly free every popped node to prevent kernel heap exhaustion.",
                    "benefit": "Intercepts memory leaks and pointer corruption before software is flashed to hardware.",
                },
                {
                    "use_case": "Automated Pointer Safety & Stack Underflow Triage",
                    "example": "When an empty stack receives POP or PEEK, the agent ensures the program safely outputs 'UNDERFLOW' without null pointer dereference crashes.",
                    "benefit": "Eliminates segmentation faults (0xC0000005) in student lab submissions.",
                },
                {
                    "use_case": "Modular Object-Oriented Architecture Verification in C",
                    "example": "Enforces separation of concerns across push(), pop(), and free_stack() helper functions rather than monolithic main() implementations.",
                    "benefit": "Instills industrial software design patterns in undergraduate engineers.",
                },
            ],
            "limitations": [
                {
                    "limitation": "Short-Lived Execution Masking Heap Fragmentation",
                    "example": "A student's stack program exits after 10 operations without triggering OS heap fragmentation that only manifests after millions of allocations.",
                    "mitigation": "Execute fuzzing stress tests with 100,000+ random interleaved push/pop operations under ASan instrumentation.",
                },
                {
                    "limitation": "Compiler Inlining of Small Allocators",
                    "example": "GCC at -O3 may inline small node structs or optimize them into stack frames, potentially bypassing certain static heap checks.",
                    "mitigation": "Evaluate submissions under both -O0 (raw pointer inspection) and -O2 (optimized safety).",
                },
            ],
        },
        "palindrome_checker": {
            "usefulness": [
                {
                    "use_case": "Bioinformatics & DNA Sequence Analysis",
                    "example": "Verifies algorithms checking reverse-complement genetic palindromes and restriction enzyme recognition sites.",
                    "benefit": "Enforces linear O(N) sequence parsing with zero memory overhead.",
                },
                {
                    "use_case": "String Processing & Buffer Sanitization Screening",
                    "example": "Tests handling of punctuation, multi-word phrases with spaces ('step on no pets'), and odd vs even length palindromes.",
                    "benefit": "Validates boundary string safety and prevents buffer overruns.",
                },
            ],
            "limitations": [
                {
                    "limitation": "ASCII Assumptions on Multi-Byte UTF-8 Runes",
                    "example": "A submission passing all ASCII tests fails when given multi-byte UTF-8 accented characters like 'é' or non-Latin scripts.",
                    "mitigation": "Incorporate wide-character wchar_t / UTF-8 multi-byte test suites into language rules.",
                },
            ],
        },
        "binary_search": {
            "usefulness": [
                {
                    "use_case": "Logarithmic Algorithmic Gating (O(log N) Enforcement)",
                    "example": "Verifies that students execute true divide-and-conquer binary search rather than passing with linear O(N) scans on sorted arrays.",
                    "benefit": "Docks points on candidates who submit naive loops for logarithmic search questions.",
                },
                {
                    "use_case": "Integer Midpoint Overflow Bug Detection",
                    "example": "Catches the infamous (low + high) / 2 signed overflow bug when searching arrays with large indices, enforcing low + (high - low) / 2.",
                    "benefit": "Teaches robust numerical boundary handling in core algorithms.",
                },
            ],
            "limitations": [
                {
                    "limitation": "Small Array Size Anomaly",
                    "example": "On very small arrays (N < 16), linear search can run faster than binary search due to branch prediction and CPU prefetching.",
                    "mitigation": "Run complexity timing benchmarks on array sizes N >= 1,000 to isolate asymptotic scaling.",
                },
            ],
        },
        "add_two_integers": {
            "usefulness": [
                {
                    "use_case": "Coding-interview and hiring screens",
                    "example": "A company runs 500 candidate submissions for an 'add two integers safely' task. The agent ranks them by correctness, edge-case handling and memory safety, and gives an explainable per-metric score.",
                    "benefit": "Fast first-round filtering where every rejection can be justified metric by metric.",
                },
                {
                    "use_case": "Plagiarism and LLM-copy triage for instructors",
                    "example": "Two submissions reach a similarity of 0.93 against the 0.85 threshold, so the agent raises a flag in the report. The instructor reviews only those pairs instead of all 300.",
                    "benefit": "Saves review time by narrowing manual checking to suspicious cases.",
                },
                {
                    "use_case": "Continuous feedback in large-enrollment university CS labs",
                    "example": "400 students submitting weekly lab assignments get instant, reproducible feedback at 2 AM without waiting days for TA grading.",
                    "benefit": "Accelerates student learning cycle and unburdens teaching assistants.",
                },
                {
                    "use_case": "CI/CD regression gating for mission-critical C software",
                    "example": "Pull requests must achieve 100/100 across correctness, sanitizers, and complexity bounds before merging into embedded systems firmware.",
                    "benefit": "Intercepts memory leaks and algorithmic latency regressions before production deployment.",
                },
            ],
            "limitations": [
                {
                    "limitation": "Tests cannot prove correctness",
                    "example": "A submission passes all 10 hidden tests but fails when the input has extra whitespace or a trailing newline that no test covers. The agent still reports 10/10.",
                    "mitigation": "The agent should create its own extra tricky test inputs and compare the student's answers with the answers of a correct program.",
                },
                {
                    "limitation": "Wall-clock timing curves are noisy on shared or virtualized machines",
                    "example": "A student's O(1) submission runs in 2ms on one execution, but during background OS scheduling spikes to 28ms, distorting empirical complexity estimation.",
                    "mitigation": "Normalize timings against a simultaneous baseline kernel or measure hardware instruction counts / CPU cycles instead of raw wall-clock time.",
                },
                {
                    "limitation": "Surface similarity can be deceived by structural refactoring and obfuscation",
                    "example": "A student copies code from a peer but reorders independent statements, inserts dead variables, or wraps expressions in macros, dropping lexical n-gram similarity below 0.85.",
                    "mitigation": "Synthesize control-flow graphs (CFG) and compare normalized intermediate representations (LLVM IR / AST) rather than token text.",
                },
                {
                    "limitation": "Compiler optimizations may mask undefined behavior or dead loops",
                    "example": "An uninitialized variable or dead infinite loop is eliminated by GCC at -O2 optimization level, allowing a flawed submission to pass smoke tests.",
                    "mitigation": "Compile and test across multiple optimization tiers (-O0, -O2, -Og) with ASan/UBSan instrumentation.",
                },
            ],
        },
    }

    @classmethod
    def get_problem_profile(cls, problem_name: str) -> Dict[str, Any]:
        """Returns problem-specific usefulness and limitations profile."""
        clean_name = problem_name.lower().replace("-", "_")
        for k in cls.PROBLEM_PROFILES:
            if k in clean_name:
                res = dict(cls.PROBLEM_PROFILES[k])
                res["problem"] = k
                return res
        res = dict(cls.PROBLEM_PROFILES["add_two_integers"])
        res["problem"] = "add_two_integers"
        return res

    @classmethod
    def compute_deductions(cls, report_data: Dict[str, Any]) -> List[str]:
        """Computes on-point, mathematical explanations for every point deducted."""
        deductions: List[str] = []
        metrics = report_data.get("metrics", [])

        for m in metrics:
            name = m.get("name", "")
            weight = m.get("weight", 0.0)
            score = m.get("score", 0.0)
            max_points = weight * 100.0
            earned_points = m.get("contribution", score * max_points)
            lost_points = round(max_points - earned_points, 1)

            if lost_points > 0.05:
                feedback = m.get("feedback", "")
                evidence = m.get("evidence", {})
                detail = feedback

                if name == "modularity" and "only main" in feedback.lower():
                    detail = f"Only main() defined; expected at least {evidence.get('expected_min', 2)} functions (core logic should be in a helper function)."
                elif name == "structure":
                    detail = f"Structural deficiencies: {feedback}."
                elif name == "complexity":
                    detail = f"Algorithmic complexity penalty: {feedback}."
                elif name == "memory_safety":
                    detail = f"Memory safety violation: {feedback}."
                elif name == "syntax":
                    detail = f"Compiler warnings/errors detected: {feedback}."
                elif name == "readability":
                    detail = f"Readability/style deficiencies: {feedback}."
                elif name == "originality":
                    detail = f"Plagiarism/similarity penalty: {feedback}."
                elif name == "correctness":
                    passed = evidence.get("tests_passed", 0)
                    total = evidence.get("tests_total", 0)
                    detail = f"Failed {total - passed} of {total} test cases: {feedback}."

                deductions.append(f"[{name.upper()}] -{lost_points:.1f} pts: {detail}")

        return deductions

    @classmethod
    def generate_json_report(cls, report_data: Dict[str, Any], output_path: str | Path) -> str:
        """Saves machine-readable JSON report with deductions and problem-specific profiles."""
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Attach deductions
        report_data["deductions"] = cls.compute_deductions(report_data)

        # Attach problem-specific profile if not already custom
        problem = report_data.get("problem", "unknown")
        profile = cls.get_problem_profile(problem)
        if "usefulness_limitations" not in report_data or not report_data["usefulness_limitations"]:
            report_data["usefulness_limitations"] = profile

        json_str = json.dumps(report_data, indent=2)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return json_str

    @classmethod
    def generate_text_report(cls, report_data: Dict[str, Any], output_path: str | Path) -> str:
        """Saves human-readable text report with on-point deduction analysis."""
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = []
        submission_name = report_data.get("submission", "unknown.c")
        grade = report_data.get("grade", 0.0)
        problem = report_data.get("problem", "unknown")

        lines.append(f"===== Grading report for {submission_name} =====")
        lines.append(f"Problem: {problem}")
        lines.append(f"Overall grade: {grade:.1f} / 100")
        lines.append(f"{'Metric':<14} {'Weight':<6} {'Score':<6} {'Contribution':<12} {'Verdict'}")

        for m in report_data.get("metrics", []):
            name = m.get("name", "")
            weight_pct = int(round(m.get("weight", 0.0) * 100))
            score_norm = m.get("score", 0.0)
            score_str = f"{int(round(score_norm * weight_pct))}/{weight_pct}"
            contrib = f"{m.get('contribution', 0.0):.1f}"
            feedback = m.get("feedback", "")
            lines.append(f"{name:<14} {weight_pct:<6} {score_str:<6} {contrib:<12} {feedback}")

        # On-Point Deduction Analysis
        deductions = cls.compute_deductions(report_data)
        if deductions:
            lines.append("")
            lines.append("--- Why Your Grade Decreased (Deduction Analysis) ---")
            for d in deductions:
                lines.append(f"- {d}")
        else:
            lines.append("")
            lines.append("--- Perfect Score: Zero Point Deductions! ---")

        # Failing test cases
        failing_tests = []
        for m in report_data.get("metrics", []):
            ev = m.get("evidence", {})
            if "failing" in ev and ev["failing"]:
                failing_tests.extend(ev["failing"])

        if failing_tests:
            lines.append("")
            lines.append("--- Where you failed ---")
            for idx, fail in enumerate(failing_tests, 1):
                inp = fail.get("input", "")
                exp = fail.get("expected", "")
                got = fail.get("got", "")
                note = fail.get("note", "")
                lines.append(f"Test {idx:02d} INPUT: {inp}")
                lines.append(f"EXPECTED: {exp}")
                lines.append(f"GOT: {got if got else f'({note})'}")
                explanation = CounterTestGenerator.explain_failure(inp, got, exp)
                lines.append(f"WHY: {explanation}")

        # Suggestions
        suggestions = report_data.get("suggestions", [])
        if suggestions:
            lines.append("")
            lines.append("--- Suggestions to raise the grade ---")
            for s in suggestions:
                lines.append(f"- {s}")

        # Problem-Specific Usefulness & Limitations
        profile = cls.get_problem_profile(problem)
        usefulness_list = profile.get("usefulness", [])
        limits_list = profile.get("limitations", [])

        lines.append("")
        lines.append(f"—-- Usefulness & limitations for {problem} —--")
        lines.append("Useful for:")
        for idx, u in enumerate(usefulness_list, 1):
            lines.append(f"{idx}. {u['use_case']}")
            lines.append(f"Example: {u['example']}")
            lines.append(f"Benefit: {u['benefit']}")
            lines.append("")

        lines.append(f"Limits of this report ({problem}):")
        for idx, lim in enumerate(limits_list, 1):
            lines.append(f"{idx}. {lim['limitation']}")
            lines.append(f"Example: {lim['example']}")
            fix_label = "mitigation" if "mitigation" in lim else "Fix"
            lines.append(f"{fix_label.capitalize()}: {lim.get(fix_label, lim.get('mitigation', ''))}")
            lines.append("")

        text_content = "\n".join(lines).strip() + "\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        return text_content
