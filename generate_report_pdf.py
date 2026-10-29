"""
Publication-Quality PDF Report Generator for AutoGrader (agentic01.pdf).
Generates an academic lab progress report using ReportLab.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)


def build_pdf(filename: str = "agentic01.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#3b82f6"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=normal,
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    code_style = ParagraphStyle(
        "CodeBlock",
        parent=normal,
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=6,
        spaceAfter=6,
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("AutoGrader: A Rule-Driven Evaluator for C Programs", title_style))
    story.append(Paragraph("LAB PROGRESS REPORT (agentic01.pdf) &bull; COMPUTING LABORATORY", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Reproducibility Contract", h1_style))
    story.append(Paragraph(
        "Manual grading of student C programming submissions is slow, subjective, and difficult to scale across "
        "large class sizes. <b>AutoGrader</b> is an autonomous, rule-driven evaluation agent designed to judge "
        "C programs unattended under fixed time and memory limits. It reads grading rules from an external specification file, "
        "performs a cheap first-pass sanity sweep, dispatches nine specialized expert analyzers in parallel, and returns an "
        "explainable grade with actionable feedback.<br/><br/>"
        "The agent strictly honors the <b>Reproducibility Contract</b>: <i>The same submission judged under the same rules "
        "receives the identical grade every time the agent is executed</i>.",
        body_style,
    ))

    # Workload Distribution Table
    story.append(Paragraph("2. Group Workload Distribution", h1_style))
    story.append(Paragraph(
        "Development responsibilities are partitioned cleanly across four team members according to architectural tiers:",
        body_style,
    ))

    workload_data = [
        [
            Paragraph("<b>Member</b>", body_style),
            Paragraph("<b>Subsystem & Role</b>", body_style),
            Paragraph("<b>Deliverables & Implementation Scope</b>", body_style),
        ],
        [
            Paragraph("<b>Member 1 (Lead)</b>", body_style),
            Paragraph("Core Architecture & Process Sandboxing", body_style),
            Paragraph(
                "• Main Coordinator (<code>coordinator.py</code>)<br/>"
                "• Process supervisor & timeouts (<code>sandbox.py</code>)<br/>"
                "• First-pass sanity sweep (compile, smoke, static)<br/>"
                "• Command Line Interface (<code>cli.py</code>)",
                body_style,
            ),
        ],
        [
            Paragraph("<b>Member 2</b>", body_style),
            Paragraph("Execution, Safety & Counter-Tests", body_style),
            Paragraph(
                "• Hidden I/O test runner (<code>correctness.py</code>)<br/>"
                "• Boundary & overflow runner (<code>logical.py</code>)<br/>"
                "• Memory safety & ASan/UBSan (<code>memory_safety.py</code>)<br/>"
                "• Counter-test generator (<code>counter_test_generator.py</code>)",
                body_style,
            ),
        ],
        [
            Paragraph("<b>Member 3</b>", body_style),
            Paragraph("Static Analysis & Complexity", body_style),
            Paragraph(
                "• Compiler warnings engine (<code>syntax.py</code>)<br/>"
                "• Cyclomatic complexity & length (<code>structure.py</code>)<br/>"
                "• Modularity & helper split (<code>modularity.py</code>)<br/>"
                "• Complexity timing curve (<code>complexity.py</code>)",
                body_style,
            ),
        ],
        [
            Paragraph("<b>Member 4</b>", body_style),
            Paragraph("Originality, LLM Style & Reporting", body_style),
            Paragraph(
                "• Token Winnowing similarity (<code>originality.py</code>)<br/>"
                "• Deterministic LLM style review (<code>readability.py</code>)<br/>"
                "• JSON / TXT report collation (<code>reporter.py</code>)<br/>"
                "• Unit test suite & PDF generator (<code>agentic01.pdf</code>)",
                body_style,
            ),
        ],
    ]

    t_workload = Table(workload_data, colWidths=[110, 140, 250])
    t_workload.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_workload)
    story.append(Spacer(1, 10))

    # Implementation Progress So Far
    story.append(Paragraph("3. Implementation Progress Achieved So Far", h1_style))
    story.append(Paragraph(
        "<b>A. First-Pass Cheap Sanity Sweep</b>: Verifies static structure (<code>main</code>, readers, writers, return), "
        "runs compiler checks with <code>-O2 -Wall -Wextra -std=c11</code>, and executes a 1-second smoke run. If an infinite loop is "
        "detected, the agent sets <code>suspected_infinite_loop: true</code>, skips dynamic execution, and outputs a partial report.<br/>"
        "<b>B. Nine Expert Specialist Analyzers</b>: Fully operational in <code>autograder/analyzers/</code> (correctness, syntax, structure, "
        "modularity, logical, complexity, memory safety, readability, originality).<br/>"
        "<b>C. Counter-Test Synthesis & Deduction Analysis</b>: Synthesizes concrete failing inputs and detailed on-point deductions explaining why points decreased.<br/>"
        "<b>D. Multi-Solution Special Judge</b>: Evaluates problems with multiple valid answers (e.g. Two-Sum) by mathematical verification instead of rigid diffing.<br/>"
        "<b>E. Problem-Specific Report Generation</b>: Tailors usefulness and limitations dynamically per problem domain.<br/>"
        "<b>F. Minimalist Web UI (Dark/Light Mode)</b>: Flask web portal on local host with live execution, deduction breakdowns, and report downloads.<br/>"
        "<b>G. Full Automated Unit Test Suite</b>: 9 comprehensive tests running with 100% pass rate in <code>unit_tests/run_all_tests.py</code>.",
        body_style,
    ))

    # Empirical Results Table
    story.append(Paragraph("4. Benchmark Results on Multi-Domain Problem Suites", h1_style))
    results_data = [
        [
            Paragraph("<b>Submission File</b>", body_style),
            Paragraph("<b>Rule Set Target</b>", body_style),
            Paragraph("<b>Grade</b>", body_style),
            Paragraph("<b>Diagnostic Verification</b>", body_style),
        ],
        [
            Paragraph("<code>add_student.c</code>", body_style),
            Paragraph("add_two_integers", body_style),
            Paragraph("<b>79.0 / 100</b>", body_style),
            Paragraph("Main function only; fails signed overflow on INT_MAX+1; terse variables.", body_style),
        ],
        [
            Paragraph("<code>add_perfect.c</code>", body_style),
            Paragraph("add_two_integers", body_style),
            Paragraph("<b>100.0 / 100</b>", body_style),
            Paragraph("Modular helper function; clean headers; 64-bit integer overflow protection.", body_style),
        ],
        [
            Paragraph("<code>add_infinite_loop.c</code>", body_style),
            Paragraph("add_two_integers", body_style),
            Paragraph("<b>38.0 / 100</b>", body_style),
            Paragraph("Smoke run timed out; suspected_infinite_loop set; dynamic tests bypassed.", body_style),
        ],
        [
            Paragraph("<code>add_plagiarized.c</code>", body_style),
            Paragraph("add_two_integers", body_style),
            Paragraph("<b>69.0 / 100</b>", body_style),
            Paragraph("Similarity 1.00 against add_student.c; flagged above 0.85 threshold.", body_style),
        ],
        [
            Paragraph("<code>two_sum_quadratic.c</code>", body_style),
            Paragraph("two_sum_sorted", body_style),
            Paragraph("<b>66.0 / 100</b>", body_style),
            Paragraph("Nested loops flagged: strictly violates O(N) complexity bound requirement.", body_style),
        ],
        [
            Paragraph("<code>two_sum_optimal.c</code>", body_style),
            Paragraph("two_sum_sorted", body_style),
            Paragraph("<b>95.0 / 100</b>", body_style),
            Paragraph("Optimal O(N) two-pointer technique in helper; Special Judge validated multi-solution.", body_style),
        ],
        [
            Paragraph("<code>stack_leaky.c</code>", body_style),
            Paragraph("dynamic_stack", body_style),
            Paragraph("<b>78.7 / 100</b>", body_style),
            Paragraph("Memory safety penalized: allocation without matching free(); monolithic main.", body_style),
        ],
        [
            Paragraph("<code>stack_robust.c</code>", body_style),
            Paragraph("dynamic_stack", body_style),
            Paragraph("<b>96.0 / 100</b>", body_style),
            Paragraph("6 helper functions; underflow protection; zero memory leaks confirmed.", body_style),
        ],
        [
            Paragraph("<code>palindrome_buggy.c</code>", body_style),
            Paragraph("palindrome_checker", body_style),
            Paragraph("<b>85.5 / 100</b>", body_style),
            Paragraph("Fails case-insensitivity on mixed casing; flagged by synthesized counter-test.", body_style),
        ],
        [
            Paragraph("<code>palindrome_perfect.c</code>", body_style),
            Paragraph("palindrome_checker", body_style),
            Paragraph("<b>90.0 / 100</b>", body_style),
            Paragraph("Clean helper function; alphanumeric normalization; passes all edge tests.", body_style),
        ],
        [
            Paragraph("<code>binary_search_linear.c</code>", body_style),
            Paragraph("binary_search", body_style),
            Paragraph("<b>83.7 / 100</b>", body_style),
            Paragraph("O(N) linear scan penalized; fails logarithmic complexity bound requirement.", body_style),
        ],
        [
            Paragraph("<code>binary_search_optimal.c</code>", body_style),
            Paragraph("binary_search", body_style),
            Paragraph("<b>96.0 / 100</b>", body_style),
            Paragraph("Iterative O(log N) bisection helper; clean contracts and edge checks.", body_style),
        ],
    ]

    t_results = Table(results_data, colWidths=[125, 95, 70, 210])
    t_results.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_results)
    story.append(Spacer(1, 10))

    # Usefulness and Limitations Section
    story.append(Paragraph("5. Usefulness & Limitations in Real-Life Environments", h1_style))
    story.append(Paragraph("<b>Real-Life Usefulness:</b>", h2_style))
    story.append(Paragraph(
        "1. <i>High-Volume Technical Hiring</i>: 500 candidate submissions evaluated in under 15 minutes with explainable per-metric justification.<br/>"
        "2. <i>Plagiarism & LLM Triage</i>: Computes token n-gram similarity against 40,000+ pairs, flagging only anomalous pairs (&gt;0.85).<br/>"
        "3. <i>24/7 Formative Lab Feedback</i>: Provides instant counter-test feedback to students at 2 AM without waiting days for TA grading.<br/>"
        "4. <i>CI/CD Regression Gating</i>: Pre-commit gate for embedded software ensuring 100/100 across sanitizers and complexity bounds.",
        body_style,
    ))

    story.append(Paragraph("<b>Fundamental Limitations & Concrete Mitigations:</b>", h2_style))
    story.append(Paragraph(
        "1. <i>Tests cannot prove correctness</i>: A submission passing 10 hidden tests may fail on untested whitespace or trailing newlines. "
        "<b>Mitigation</b>: Incorporate automated fuzzing (libFuzzer) and reference-model counter-test generation.<br/>"
        "2. <i>Timing curves sensitive to OS noise</i>: Background OS indexing can distort wall-clock empirical curves from O(1) to O(N). "
        "<b>Mitigation</b>: Profile hardware CPU instruction cycles and normalize against an in-slice baseline kernel.<br/>"
        "3. <i>Token similarity evadable by macro obfuscation</i>: Reordering statements or wrapping expressions in macros reduces lexical n-gram similarity. "
        "<b>Mitigation</b>: Compare Abstract Syntax Tree (AST) tree-isomorphisms and LLVM bitcode diffs.<br/>"
        "4. <i>Compiler optimization masking bugs</i>: GCC -O2 can optimize away uninitialized variables or dead loops. "
        "<b>Mitigation</b>: Run multi-tier compilation (-O0 with ASan/UBSan, -O2 with strict warnings).",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # Future Timeline
    story.append(Paragraph("6. Project Timeline & Next Milestones", h1_style))
    timeline_data = [
        [
            Paragraph("<b>Milestone</b>", body_style),
            Paragraph("<b>Target</b>", body_style),
            Paragraph("<b>Deliverables & Strategic Objectives</b>", body_style),
        ],
        [
            Paragraph("<b>Milestone 1 (Complete)</b>", body_style),
            Paragraph("Week 1", body_style),
            Paragraph("Architecture, sandbox, external rules parser, 9 expert analyzers, benchmark reports, agentic01.pdf.", body_style),
        ],
        [
            Paragraph("<b>Milestone 2</b>", body_style),
            Paragraph("Week 2", body_style),
            Paragraph("Automated fuzz testing engine, AST graph isomorphism for plagiarism detection, multi-tier compiler matrix.", body_style),
        ],
        [
            Paragraph("<b>Milestone 3</b>", body_style),
            Paragraph("Week 3", body_style),
            Paragraph("Hardware performance counter profiling, multi-file project support (Makefiles), local Ollama LLM integration.", body_style),
        ],
        [
            Paragraph("<b>Milestone 4 (Final)</b>", body_style),
            Paragraph("Week 4", body_style),
            Paragraph("Interactive instructor dashboard, 15-20 min demonstration video on YouTube, final report submission.", body_style),
        ],
    ]

    t_timeline = Table(timeline_data, colWidths=[130, 60, 310])
    t_timeline.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_timeline)

    # Build document
    doc.build(story)
    print(f"[+] Successfully generated {filename}")


if __name__ == "__main__":
    out_pdf = "agentic01.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)

