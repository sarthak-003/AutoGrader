# Project Progress Report: AutoGrader Agent (agentic01.pdf)

**Course**: Computing Laboratory / Agentic AI Systems  
**Project**: AutoGrader: A Rule-Driven Evaluator for C Programs  
**Date**: October 2026  
**Document**: Lab Progress Report (`agentic01.pdf`)  

---

## 1. Executive Summary

Manual grading of student C programming submissions suffers from chronic inconsistency, subjective bias, latency, and inability to scale across large class enrollments. This project designs and implements **AutoGrader**, an autonomous, rule-driven evaluation agent capable of judging student C submissions unattended. 

AutoGrader is strictly governed by the **Reproducibility Contract**:
$$\text{Submission} + \text{Rules} \longrightarrow \text{Same Grade}$$

The agent reads instructor requirements from external JSON rules files, executes code inside an isolated process supervisor enforcing time and memory caps, performs a cheap first-pass sanity sweep, dispatches expert specialist analyzers in parallel, and collates the resulting evidence into both machine-readable JSON and student-facing diagnostic reports.

---

## 2. Workload Distribution Among Group Members

To ensure robust modularity, accountability, and parallel development, responsibilities have been partitioned across the four group members according to distinct system layers:

| Member | Role / Area | Key Responsibilities & Deliverables |
| :--- | :--- | :--- |
| **Member 1 (Lead)** | **Core Architecture & Orchestration** | • Coordinator engine (`autograder/coordinator.py`)<br>• First-pass sanity sweep (compile check, smoke run, static sanity)<br>• Process supervisor & sandbox (`autograder/sandbox.py`)<br>• Top-level CLI and batch runner (`autograder/cli.py`) |
| **Member 2** | **Correctness, Safety & Execution Analyzers** | • Hidden I/O test suite runner (`autograder/analyzers/correctness.py`)<br>• Edge case runner & boundary tests (`autograder/analyzers/logical.py`)<br>• ASan/UBSan sanitizer & memory leak analyzer (`autograder/analyzers/memory_safety.py`)<br>• Counter-test & corner case generator (`autograder/counter_test_generator.py`) |
| **Member 3** | **Static, Structural & Complexity Analyzers** | • Compiler warning parser (`autograder/analyzers/syntax.py`)<br>• Cyclomatic complexity & function length (`autograder/analyzers/structure.py`)<br>• Modularity & helper decomposition analyzer (`autograder/analyzers/modularity.py`)<br>• Complexity estimator with timing curves (`autograder/analyzers/complexity.py`) |
| **Member 4** | **Originality, LLM Style & Reporting** | • Token Winnowing / Jaccard similarity analyzer (`autograder/analyzers/originality.py`)<br>• LLM / heuristic deterministic code style reviewer (`autograder/analyzers/readability.py`)<br>• Report collator for JSON/TXT outputs (`autograder/reporter.py`)<br>• Unit test suite & report PDF generation (`generate_report_pdf.py`) |

---

## 3. System Architecture & Implementation Plan

AutoGrader adopts a three-tier agentic architecture:

```
┌────────────────────────────────────────────────────────┐
│               External Rule Specification              │
│       rules/*.json (Problem, Time/Mem Limits, Metrics) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Main Agent (Grading Coordinator)            │
│  Phase 1: First-Pass Sanity Sweep                      │
│    • Static Sanity Check (main, reader, writer, return)│
│    • Sandbox Compilation Check (gcc -O2 -Wall -Wextra) │
│    • Smoke Run (timeout/crash detection)               │
└───────────────────────────┬────────────────────────────┘
                            │ (If smoke run times out:
                            │  set suspected_infinite_loop,
                            │  skip dynamic analyzers)
                            ▼
┌────────────────────────────────────────────────────────┐
│          Parallel Dispatch to Expert Analyzers         │
├───────────────────────────┬────────────────────────────┤
│   Dynamic (Execution)     │     Static (Source Only)   │
│   • io_tests              │     • compiler_warnings    │
│   • edge_case_runner      │     • static_analysis      │
│   • complexity_estimator  │     • function_split       │
│   • sanitizer_run         │     • llm_review           │
│                           │     • similarity_flag      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              Aggregation & Report Collation            │
│    • Weighted Grade Calculation (0-100)                │
│    • Counter-Test Case & Failure Explanation           │
│    • Machine-readable reports/<name>.json              │
│    • Student-readable reports/<name>.txt               │
└────────────────────────────────────────────────────────┘
```

---

## 4. Progress So Far

All core components scheduled for initial delivery have been successfully implemented and verified:
1. **Rule-Driven Configuration**: Defined clean schemas for external rule sets, supporting dynamic weight assignment, per-analyzer parameter slicing, and SHA-256 provenance hashing.
2. **Process Sandboxing**: Implemented `ProcessSandbox` with cross-platform process supervision, hard timeouts, memory limit monitoring, and crash code interception (Windows NTSTATUS `0xC0000005`, `0xC0000094`, and POSIX signals).
3. **First-Pass Cheap Sanity Sweep**: Fully operational. Successfully detects infinite loops (`while(1)`) during the smoke run, automatically tags `suspected_infinite_loop: true`, skips dynamic execution, and emits a partial report.
4. **All 9 Expert Analyzers**: Implemented and registered in the modular analyzer registry.
5. **Adversarial Counter-Test Generation**: Formulates concrete explanations ("WHY: signed overflow on 32-bit integer addition") and displays input, expected output, and actual output side-by-side.
6. **Empirical Verification on Sample Submissions**:
   - `add_student.c` (PDF sample): Evaluated with 79.0/100, capturing the exact deficiencies outlined in the specification (single main function, terse variable names, signed overflow).
   - `add_perfect.c`: Achieved 100.0/100 with zero compiler diagnostics, clean modular helper decomposition, and 64-bit bounds handling.
   - `add_infinite_loop.c`: Successfully timed out safely, skipped dynamic tests, and scored 38.0/100 without stalling the host runner.
   - `add_plagiarized.c`: Flagged for plagiarism with 1.00 similarity against `add_student.c`.
7. **Automated Unit Test Suite**: 9 unit tests passing cleanly in `unit_tests/run_all_tests.py`, verifying reproducibility, sandboxing, and analyzer precision.

---

## 5. Future Plan and Milestone Timeline

| Phase / Milestone | Target Week | Key Deliverables |
| :--- | :--- | :--- |
| **Milestone 1** (Current) | **Week 1** | • Core coordinator, sandbox, external rules parser, 9 expert analyzers.<br>• Verified sample submissions, JSON/TXT reports, and `agentic01.pdf` progress report. |
| **Milestone 2** | **Week 2** | • Fuzzing integration (AFL / libFuzzer) to automatically synthesize edge cases.<br>• LLVM IR / Abstract Syntax Tree (AST) graph isomorphism for originality analysis.<br>• Multi-optimization compiler matrix (-O0, -O2, -Og). |
| **Milestone 3** | **Week 3** | • High-precision hardware performance counter profiling (perf / CPU instruction cycles).<br>• Support for multi-file C submissions (Makefiles / CMake targets).<br>• Local Ollama / Groq API connector with fallback to deterministic local rules. |
| **Milestone 4** | **Week 4** | • Interactive Web UI / Dashboard for instructors.<br>• 15–20 minute video demonstration recording and YouTube upload.<br>• Final project comprehensive report and open-source GitHub release. |

