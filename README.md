# AutoGrader: A Rule-Driven Evaluator for C Programs

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Architecture: Agentic](https://img.shields.io/badge/architecture-Rule--Driven%20Agentic-purple.svg)]()
[![Reproducibility: Deterministic](https://img.shields.io/badge/contract-Deterministic%20Grading-brightgreen.svg)]()

> **AutoGrader** is an intelligent, rule-driven evaluation agent designed to judge student C programs autonomously, safely, and unattended under strict time and memory limits.

---

## Table of Contents
1. [Core Mission & Reproducibility Contract](#core-mission--reproducibility-contract)
2. [System Architecture](#system-architecture)
3. [Project Directory Layout](#project-directory-layout)
4. [Installation & Setup](#installation--setup)
5. [Rule Specification (Instructor Configuration)](#rule-specification-instructor-configuration)
6. [Specialist Analyzers Catalog](#specialist-analyzers-catalog)
7. [Running the AutoGrader](#running-the-autograder)
8. [Sample Submissions & Benchmark Results](#sample-submissions--benchmark-results)
9. [Usefulness and Limitations in Real Life](#usefulness-and-limitations-in-real-life)
10. [Deliverables Checklist](#deliverables-checklist)

---

## Core Mission & Reproducibility Contract

Manual grading of student C programming assignments suffers from human fatigue, subjectivity, slow turnaround times, and lack of scalability across large class sizes. 

AutoGrader completely automates the evaluation pipeline:
- **Safety**: Isolates binary execution under fixed time (e.g. 1.0s) and memory limits (e.g. 64 MB), surviving infinite loops and segmentation faults.
- **Rule-Driven**: Rules, thresholds, metrics, and weights are maintained strictly outside source code in JSON configuration files. Modifying grading criteria never requires modifying the agent.
- **Explainability**: For any incorrect submission, the agent synthesizes the specific failing input, expected output, got output, and a precise engineering explanation ("WHY").
- **Plagiarism & AI Copy Detection**: Identifies token-level structural similarity against peer submissions and online LLM templates.

### The Reproducibility Contract
$$\text{Submission} + \text{Grading Rules} \implies \text{Identical Grade}$$
Judging the same submission under the identical rule set will always yield the exact same grade and diagnostics, guaranteed through deterministic analysis and fixed pseudo-random seeds (`temperature=0, seed=42`).

---

## System Architecture

AutoGrader coordinates evaluation through a three-phase agentic pipeline:

```mermaid
flowchart TD
    subgraph Input ["Input Layer"]
        sub["Student Submission (.c)"]
        rules["External Rules (.json)"]
    end

    subgraph Phase1 ["Phase 1: First-Pass Sanity Sweep"]
        static["Static Sanity Check\n(main, reader, writer, return)"]
        compile["Sandboxed Compilation\ngcc -O2 -Wall -Wextra -std=c11"]
        smoke["Smoke Run (1s, 64MB)\nDetects crashes & loops"]
    end

    subgraph Dispatch ["Phase 2: Expert Analyzer Dispatch"]
        direction TB
        subgraph Dynamic ["Dynamic Execution Analyzers"]
            an_correct["io_tests\n(Hidden test runner)"]
            an_logic["edge_case_runner\n(Zeros, negatives, overflow)"]
            an_complex["complexity_estimator\n(Timing curve & loop depth)"]
            an_mem["sanitizer_run\n(ASan, UBSan, leak check)"]
        end
        subgraph Static ["Static Source Analyzers"]
            an_syntax["compiler_warnings\n(Warning diagnostics)"]
            an_struct["static_analysis\n(Cyclomatic CCN, function LOC)"]
            an_mod["function_split\n(Modular helper verification)"]
            an_read["llm_review\n(Deterministic style rater)"]
            an_orig["similarity_flag\n(Token Winnowing Jaccard)"]
        end
    end

    subgraph Phase3 ["Phase 3: Aggregation & Collation"]
        weight["Weighted Summation (0-100)\nRules Provenance SHA-256"]
        counter["Counter-Test & Explanation Generator"]
        rep_json["Machine Report (reports/*.json)"]
        rep_txt["Student Report (reports/*.txt)"]
    end

    sub --> static --> compile --> smoke
    rules --> Phase1
    rules --> Dispatch

    smoke -- Clean Exit --> Dispatch
    smoke -- Timeout Detected --> |Set suspected_infinite_loop\nSkip dynamic execution| Static

    Dynamic --> Phase3
    Static --> Phase3
    Phase3 --> rep_json
    Phase3 --> rep_txt
```

---

## Project Directory Layout

```
AutoGrader/
├── README.md                           # Master project documentation
├── requirements.txt                     # Dependencies (lizard, reportlab, psutil)
├── run_grader.py                       # Top-level execution entry point
├── generate_report_pdf.py              # Publication-quality PDF report compiler
├── agentic01.pdf                       # Official Lab Deliverable Report
│
├── autograder/                         # Core agent package
│   ├── __init__.py                     # Package exports
│   ├── config.py                       # Rules schema & dataclasses
│   ├── compiler.py                     # C Compiler toolchain manager
│   ├── sandbox.py                      # Process supervisor (time & memory limits)
│   ├── counter_test_generator.py       # Counter-test & corner case generator
│   ├── coordinator.py                  # Agent orchestrator & dispatch engine
│   ├── reporter.py                     # JSON / TXT report collation engine
│   ├── cli.py                          # Command Line Interface
│   └── analyzers/                      # Expert specialist analyzers
│       ├── __init__.py                 # Dynamic analyzer registry
│       ├── base.py                     # BaseAnalyzer abstract interface
│       ├── correctness.py              # IOTestAnalyzer
│       ├── syntax.py                   # CompilerWarningsAnalyzer
│       ├── structure.py                # StaticAnalysisAnalyzer
│       ├── modularity.py               # FunctionSplitAnalyzer
│       ├── logical.py                  # EdgeCaseRunnerAnalyzer
│       ├── complexity.py               # ComplexityEstimatorAnalyzer
│       ├── memory_safety.py            # SanitizerRunAnalyzer
│       ├── readability.py              # LLMReviewAnalyzer
│       └── originality.py              # SimilarityFlagAnalyzer
│
├── rules/                              # External rule specifications
│   ├── add_two_integers.json           # Primary assignment rule set
│   ├── add_with_plagiarism_check.json  # Peer-review plagiarism rules
│   ├── reverse_array.json              # Second sample problem rules
│   └── matrix_multiply.json            # Third sample problem rules
│
├── tests/                              # Hidden test suites
│   ├── add/                            # 10 test cases including INT_MAX overflow
│   │   ├── test_01.in / test_01.out
│   │   └── ... test_10.in / test_10.out
│   └── reverse/                        # Test cases for reverse array
│
├── corpus/                             # Plagiarism corpus
│   └── add/                            # Reference & archived submissions
│       ├── ref_solution.c
│       └── student_bob.c
│
├── submissions/                        # Test student submissions
│   ├── add_student.c                   # PDF baseline (single function, overflow)
│   ├── add_perfect.c                   # 100/100 modular clean submission
│   ├── add_infinite_loop.c             # Submission with while(1) loop
│   ├── add_crash_segfault.c            # Submission with null dereference
│   ├── add_memory_leak.c               # Submission with malloc and no free
│   ├── add_plagiarized.c               # Plagiarized peer copy
│   └── add_compile_error.c             # Syntax error submission
│
├── reports/                            # Generated evaluation reports
│   ├── add_student.json / .txt
│   ├── add_perfect.json / .txt
│   └── ...
│
├── unit_tests/                         # Verification test suite
│   ├── test_sandbox.py                 # Timeouts & crash survival tests
│   ├── test_rules.py                   # Rules parsing & hash validation
│   ├── test_analyzers.py               # Analyzer unit tests
│   ├── test_reproducibility.py         # Reproducibility contract test
│   └── run_all_tests.py                # Master test runner
│
└── docs/                               # Detailed documentation
    ├── usefulness_and_limitations.md   # Deep dive on utility & edge cases
    └── agentic01_report.md             # Lab progress & workload distribution
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- GCC or Clang toolchain installed (`gcc --version`)

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Adding a New Problem Rule and Test Cases

AutoGrader is strictly modular: **creating a new assignment or problem requires zero modifications to the core agent source code**. You have three options:

### Option 1: Via the Web UI (One-Click)
1. Open the Web UI at **`http://127.0.0.1:5000`**.
2. Under section **2. Grading Rules**, click **`+ Create New Problem Rule & Testcases`**.
3. Fill in:
   - **Problem Identifier**: (e.g. `fibonacci`, `reverse_string`, `matrix_transpose`)
   - **Target Complexity**: Choose $O(1)$, $O(\log N)$, $O(N)$, or $O(N^2)$
   - **Test Case 1 Input & Output**: Provide sample input and expected output
4. Click **"Save & Register Problem"**: The agent writes `rules/<name>.json`, creates `tests/<name>/test_01.in` and `test_01.out`, and dynamically updates the rules dropdown.

### Option 2: Via the Interactive CLI Wizard (`add_problem.py`)
Run the automated problem generator:
```bash
python add_problem.py --name reverse_string --complexity "O(N)" --time-limit 2.0 --memory-limit 64
```
This automatically scaffolds:
- `rules/reverse_string.json` with all 7 default specialist analyzers configured.
- `tests/reverse_string/` populated with initial boundary test cases.

### Option 3: Manual JSON and Test File Creation
1. **Create the Rule File** `rules/<your_problem>.json`:
   ```json
   {
     "problem": "your_problem",
     "time_limit_s": 2,
     "memory_limit_mb": 64,
     "metrics": [
       { "name": "correctness", "analyzer": "io_tests", "weight": 0.30, "params": { "testset_dir": "tests/your_problem/" } },
       { "name": "complexity", "analyzer": "complexity_estimator", "weight": 0.20, "params": { "required": "O(N)" } },
       { "name": "modularity", "analyzer": "function_split", "weight": 0.20, "params": { "expect_helpers": true, "min_functions": 2 } },
       { "name": "syntax", "analyzer": "compiler_warnings", "weight": 0.15, "params": { "flags": "-Wall -Wextra -Werror -std=c11" } },
       { "name": "structure", "analyzer": "static_analysis", "weight": 0.15, "params": { "max_cyclomatic": 6, "max_function_length": 40 } }
     ]
   }
   ```
2. **Create the Hidden Test Suite** in `tests/<your_problem>/`:
   - `test_01.in` (stdin fed to binary) and `test_01.out` (expected stdout).
   - `test_02.in` and `test_02.out`, etc.
3. Run the evaluation immediately:
   ```bash
   python run_grader.py --submission submissions/student_work.c --rules rules/your_problem.json
   ```

---

## What is Ollama and What is it Used For in AutoGrader?

### What is Ollama?
[Ollama](https://ollama.ai) is an open-source, local Large Language Model runtime that allows running models like `llama3`, `codellama`, or `deepseek-coder` directly on your local computer's GPU or CPU without internet access or third-party cloud APIs.

### Why is Ollama in AutoGrader? (Four Core Roles)

1. **Automated Code Readability & Style Review (`llm_review`)**:
   Compilers (`gcc`) check syntax, and hidden test suites check numerical correctness. However, judging whether variable names are descriptive, functions are properly documented, and formatting is clean is a qualitative task. An LLM acts as an automated Teaching Assistant providing human-like style critique.

2. **100% Student Privacy & FERPA Compliance**:
   University and enterprise grading guidelines strictly prohibit transmitting student code to commercial cloud AI APIs (like OpenAI ChatGPT or Anthropic Claude). Ollama runs **completely offline on `http://127.0.0.1:11434`**, ensuring zero student code ever leaves the evaluation server.

3. **Zero API Costs for Unlimited Submissions**:
   Evaluating 500+ submissions across multiple lab assignments with cloud LLMs costs money per token. With local Ollama, inference is 100% free with zero quota limits.

4. **Deterministic Reproducibility & Zero-Dependency Fallback**:
   To strictly enforce the **Reproducibility Contract** ($\text{same code} + \text{same rules} \implies \text{identical grade}$), AutoGrader queries Ollama with deterministic parameters:
   `temperature: 0.0, seed: 42`.
   * **Graceful Fallback**: If Ollama is not installed or not running on the machine, AutoGrader automatically switches to its built-in **Deterministic Lexical AST Engine** without failing, crashing, or introducing cloud dependencies.

---

## Rule Specification (Instructor Configuration)

Grading rules reside in `rules/*.json`. Adding, reweighting, or reconfiguring metrics requires zero edits to the agent.

Example rule file (`rules/add_two_integers.json`):
```json
{
  "problem": "add_two_integers",
  "time_limit_s": 1,
  "memory_limit_mb": 64,
  "metrics": [
    {
      "name": "correctness",
      "analyzer": "io_tests",
      "weight": 0.20,
      "params": { "testset_dir": "tests/add/" }
    },
    {
      "name": "syntax",
      "analyzer": "compiler_warnings",
      "weight": 0.10,
      "params": { "flags": "-Wall -Wextra -Werror -std=c11" }
    },
    {
      "name": "structure",
      "analyzer": "static_analysis",
      "weight": 0.10,
      "params": { "max_cyclomatic": 8, "max_function_length": 40 }
    },
    {
      "name": "modularity",
      "analyzer": "function_split",
      "weight": 0.10,
      "params": { "expect_helpers": true, "min_functions": 2 }
    },
    {
      "name": "logical",
      "analyzer": "edge_case_runner",
      "weight": 0.10,
      "params": { "cases": ["negatives", "zero", "int_overflow"] }
    },
    {
      "name": "complexity",
      "analyzer": "complexity_estimator",
      "weight": 0.10,
      "params": { "required": "O(1)", "sizes": [1, 10, 100] }
    },
    {
      "name": "memory_safety",
      "analyzer": "sanitizer_run",
      "weight": 0.10,
      "params": { "flags": "-fsanitize=address,undefined" }
    },
    {
      "name": "readability",
      "analyzer": "llm_review",
      "weight": 0.10,
      "params": { "model": "llama-3.3-70b-versatile", "temperature": 0, "seed": 42 }
    },
    {
      "name": "originality",
      "analyzer": "similarity_flag",
      "weight": 0.10,
      "params": { "corpus_dir": "corpus/add/", "flag_threshold": 0.85 }
    }
  ]
}
```

---

## Specialist Analyzers Catalog

| Metric | Analyzer Name | Method / Implementation | Output & Feedback |
| :--- | :--- | :--- | :--- |
| **correctness** | `io_tests` | Runs hidden test set under time/memory caps; diffs stdout | `tests_passed / tests_total`, failing inputs & diffs |
| **syntax** | `compiler_warnings` | Compiles with `-Wall -Wextra -O2 -std=c11`; counts warnings | Counts `-Wunused`, type errors, warnings count |
| **structure** | `static_analysis` | Computes McCabe cyclomatic complexity and function length | CCN, LOC per function, checks headers and comments |
| **modularity** | `function_split` | AST regex regex parsing of function definitions | Detects helper functions vs monolithic `main()` |
| **logical** | `edge_case_runner` | Probes `INT_MAX+1`, `INT_MIN-1`, negative numbers, zeros | Pinpoints signed integer overflow and edge errors |
| **complexity** | `complexity_estimator`| Measures timing across input scales; inspects loop nesting | Confirms $O(1)$, $O(N)$, or $O(N^2)$ bounds |
| **memory_safety**| `sanitizer_run` | Runs ASan/UBSan & static allocation/deallocation matching | Pinpoints memory leaks (`malloc` without `free`) |
| **readability** | `llm_review` | Deterministic style inspection (names, comments, spacing) | Flags single-letter names, cramped lines, no comments |
| **originality** | `similarity_flag` | Token-normalized n-gram Winnowing & Jaccard similarity | Flags similarity $\ge$ threshold against corpus |

---

## Running the AutoGrader

### 1. Launch the Localhost Web UI (Minimalist B&W Interface with Dark/Light Toggle)
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.
- **Theme Toggle**: Switch between **Dark Mode** (dark background, crisp white borders and text) and **Light Mode** (clean white background, high-contrast dark elements) with instant localStorage persistence.
- **Multi-Solution Special Judge**: Problems with multiple valid outputs (e.g. Two-Sum multiple pairs) are validated mathematically, accepting any correct solution without false negatives.
- **On-Point Deduction Analysis**: Explains exactly why scores decreased under `--- Why Your Grade Decreased (Deduction Analysis) ---`.
- **Problem-Specific Reports**: Tailored Usefulness & Limitations analysis addressing the exact algorithmic domain.
- **Interactive Evaluation**: Select from sample `.c` files, upload your own `.c` file, or paste code directly.
- **Report Downloads**: Download text reports (`.txt`), machine reports (`.json`), or the lab progress report (`agentic01.pdf`) directly from the UI.

### 2. Grade a Single Submission via CLI
```bash
python run_grader.py --submission submissions/add_student.c --rules rules/add_two_integers.json
```

### 3. Batch Grade an Entire Submissions Directory
```bash
python run_grader.py --submissions-dir submissions/ --rules rules/add_two_integers.json
```

### 4. Run the Automated Unit Test Suite
```bash
python unit_tests/run_all_tests.py
```

### 5. Generate the Progress Report PDF (`agentic01.pdf`)
```bash
python generate_report_pdf.py agentic01.pdf
```

---

## Multi-Domain Problem Suites & Benchmark Results

AutoGrader is not limited to toy problems. It includes concrete, production-ready rule suites across fundamental computer science domains that demonstrate exactly why an automated agent is needed:

| Problem Domain | Rule File | What It Evaluates | Sample Submissions Tested |
| :--- | :--- | :--- | :--- |
| **Numerical & Overflow** | [`add_two_integers.json`](rules/add_two_integers.json) | Signed integer overflow on `INT_MAX+1`, underflow, single-function monolithic main, terse variable names. | `add_student.c` (79.0)<br>`add_perfect.c` (100.0)<br>`add_infinite_loop.c` (38.0) |
| **Algorithms & Multi-Solution** | [`two_sum_sorted.json`](rules/two_sum_sorted.json) | Enforces $O(N)$ two-pointer bound; penalizes $O(N^2)$ brute-force; **Special Judge** validates any mathematically valid index pair. | `two_sum_quadratic.c` (66.0)<br>`two_sum_optimal.c` (95.0) |
| **Data Structures & Memory** | [`dynamic_stack.json`](rules/dynamic_stack.json) | Tracks dynamic allocations; intercepts memory leaks (`malloc` without `free`); verifies stack underflow handling. | `stack_leaky.c` (78.7)<br>`stack_robust.c` (96.0) |
| **String Processing** | [`palindrome_checker.json`](rules/palindrome_checker.json) | Dynamic buffers, bounds safety, phrases with spaces, modular helper split `is_palindrome()`. | `palindrome_buggy.c` (85.5)<br>`palindrome_perfect.c` (90.0) |
| **Divide & Conquer Search** | [`binary_search.json`](rules/binary_search.json) | Enforces $O(\log N)$ logarithmic bisection bound; penalizes $O(N)$ linear scans; verifies absent element `-1` handling. | `binary_search_linear.c` (83.7)<br>`binary_search_optimal.c` (93.5) |
| **Plagiarism & Peer Triage** | [`add_with_plagiarism_check.json`](rules/add_with_plagiarism_check.json) | Token-normalized Winnowing & Jaccard similarity against peer submissions directory (`flag_threshold: 0.85`). | `add_plagiarized.c` (69.0 FLAGGED) |

### Benchmark Summary

| Submission | Problem Rule | Status | Grade | Highlights & Findings |
| :--- | :--- | :--- | :--- | :--- |
| `add_student.c` | `add_two_integers` | Completed | **79.0 / 100** | Fails signed integer overflow on `INT_MAX+1`; monolithic `main()`; terse variable names. |
| `add_perfect.c` | `add_two_integers` | Completed | **100.0 / 100** | Modular `safe_add` helper; 64-bit bounds protection; clean documentation; 0 warnings. |
| `add_infinite_loop.c` | `add_two_integers` | Intercepted | **38.0 / 100** | Smoke run safely killed on timeout; `suspected_infinite_loop: true`; dynamic tests bypassed. |
| `add_plagiarized.c` | `add_with_plagiarism_check` | Flagged | **69.0 / 100** | Detected 1.00 token similarity against `add_student.c`; raised `suspected_plagiarism` flag. |
| `two_sum_quadratic.c` | `two_sum_sorted` | Completed | **66.0 / 100** | Nested loops detected yielding $O(N^2)$; strictly penalizes algorithmic complexity. |
| `two_sum_optimal.c` | `two_sum_sorted` | Completed | **95.0 / 100** | Optimal $O(N)$ two-pointer linear scan in helper function; Special Judge verified multi-solution answer. |
| `stack_leaky.c` | `dynamic_stack` | Completed | **78.7 / 100** | Intercepted dynamic node allocation (`malloc`) with no matching `free()`; monolithic `main`. |
| `stack_robust.c` | `dynamic_stack` | Completed | **96.0 / 100** | 6 modular helper functions; underflow protection; zero memory leaks confirmed. |
| `palindrome_buggy.c` | `palindrome_checker` | Completed | **85.5 / 100** | Single-function main; fails mixed-case normalization; memory leak with unfreed copy. |
| `palindrome_perfect.c`| `palindrome_checker` | Completed | **90.0 / 100** | Modular `is_palindrome` helper; frees all buffers; passes all edge cases. |
| `binary_search_linear.c`| `binary_search` | Completed | **83.7 / 100** | Linear scan flagged; violates required $O(\log N)$ logarithmic complexity bound. |
| `binary_search_optimal.c`| `binary_search` | Completed | **96.0 / 100** | Logarithmic $O(\log N)$ bisection helper verified; zero compiler warnings; clean contracts. |

### Sample Output Report (`reports/add_student.txt`)
```text
===== Grading report for add_student.c =====
Overall grade: 79.0 / 100
Metric         Weight Score  Contribution Verdict
correctness    20     18/20  18.0         8/10 tests pass. Fails on INT_MAX + 1: signed overflow.
syntax         10     9/10   9.0          one -Wunused-result warning
structure      10     6/10   6.0          no documentation headers, single-block code
modularity     10     3/10   3.0          only main(); no helper
logical        10     8/10   8.0          overflow on INT_MAX+1 not handled
complexity     10     10/10  10.0         O(1) confirmed
memory_safety  10     10/10  10.0         no diagnostics
readability    10     5/10   5.0          no comments, Single-letter names, missing whitespace, cramped formatting.
originality    10     10/10  10.0         max similarity 0.43, not flagged

--- Where you failed ---
Test 01 INPUT: 2147483647 1
EXPECTED: 2147483648
GOT: -2147483648
WHY: a + b overflows on 32-bit signed ints. Use long long
or check that b <= INT_MAX - a before adding.

--- Suggestions to raise the grade ---
- Break logic into distinct visual sections and functions rather than a single monolithic block.
- Extract core logic into a helper function (e.g. int add(int a, int b)) and call it from main.
- Handle overflow explicitly with a wider integer type (e.g. long long) or bounds check b <= INT_MAX - a.
- Rename terse identifiers (e.g. a,b to lhs,rhs or num1,num2).
- Add a one-line comment above main() explaining the purpose of the program.
- Add spaces around arithmetic operators and blank lines between logical sections.
```

---

## Usefulness and Limitations in Real Life

For an exhaustive analysis, see [`docs/usefulness_and_limitations.md`](docs/usefulness_and_limitations.md).

### 4 Concrete Real-Life Use Cases
1. **High-Volume Technical Hiring Screens**: Screens 500+ candidates for systems programming roles in under 15 minutes with explainable per-metric scorecards.
2. **Plagiarism and LLM-Copy Triage**: Filters 40,000+ submission pairs in large classes, flagging only anomalous pairs exceeding the 0.85 similarity threshold.
3. **Continuous 24/7 Formative Lab Feedback**: Delivers instant diagnostic feedback and counter-test cases to students at 2 AM without waiting days for TA grading.
4. **CI/CD Quality Gating for Embedded Systems**: Enforces memory safety and complexity bounds on pull requests prior to hardware deployment.

### 4 Concrete Limitations & Engineering Mitigations
1. **Tests Cannot Prove Formal Correctness**: A program passing 10 hidden tests may fail on untested trailing whitespace.  
   *Mitigation*: Integrate automated fuzzing (`libFuzzer`) and reference-model counter-test synthesis.
2. **Timing Curves Susceptible to OS Scheduling Noise**: Background OS indexing can distort wall-clock measurements from $O(1)$ to $O(N)$.  
   *Mitigation*: Measure hardware CPU instruction cycles and normalize against concurrent in-slice baseline benchmarks.
3. **Lexical Similarity Evaded by Obfuscation**: Statement reordering and macros degrade token n-gram similarity below 0.85.  
   *Mitigation*: Perform Abstract Syntax Tree (AST) tree-isomorphism and LLVM IR bitcode graph diffing.
4. **Compiler Optimizations at -O2 Masking Semantic Bugs**: GCC optimizations can eliminate uninitialized variables or dead loops.  
   *Mitigation*: Run a multi-tier compilation matrix (`-O0` with sanitizers, `-O2` with strict warnings).

---

## Deliverables Checklist

- [x] **Complete Working Agent**: Fully modular, unattended execution pipeline in `autograder/`
- [x] **External Rules Engine**: JSON-based criteria (`rules/add_two_integers.json`, `reverse_array.json`, etc.)
- [x] **Survives Crashes & Loops**: Verified safe process supervision under strict timeouts & memory caps
- [x] **All 9 Specialist Analyzers**: `io_tests`, `compiler_warnings`, `static_analysis`, `function_split`, `edge_case_runner`, `complexity_estimator`, `sanitizer_run`, `llm_review`, `similarity_flag`
- [x] **Counter-Test & Explanation Synthesis**: Formulates exact input, expected output, actual output, and "WHY" explanation
- [x] **Sample Submissions & Benchmark Reports**: JSON and TXT reports generated in `reports/`
- [x] **Usefulness & Limitations Section**: Detailed documentation in report and `docs/usefulness_and_limitations.md`
- [x] **Lab Deliverable PDF Report (`agentic01.pdf`)**: Generated via `generate_report_pdf.py` with 4-member workload distribution and milestone timeline
- [x] **Full Unit Test Suite**: 9 unit tests passing with 100% success rate in `unit_tests/run_all_tests.py`

