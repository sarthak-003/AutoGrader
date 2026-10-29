"""
Unit tests for all expert analyzers.
"""

from pathlib import Path
from autograder.compiler import CCompiler
from autograder.sandbox import ProcessSandbox
from autograder.analyzers import (
    get_analyzer,
    StaticAnalysisAnalyzer,
    FunctionSplitAnalyzer,
    LLMReviewAnalyzer,
    SimilarityFlagAnalyzer,
)


def test_modularity_analyzer():
    analyzer = get_analyzer("function_split")
    
    # Main only
    student_src = Path("submissions/add_student.c")
    res1 = analyzer.analyze(student_src, None, {"expect_helpers": True, "min_functions": 2}, {})
    assert res1.score == 0.30
    assert "only main" in res1.feedback.lower()

    # Perfect modular
    perfect_src = Path("submissions/add_perfect.c")
    res2 = analyzer.analyze(perfect_src, None, {"expect_helpers": True, "min_functions": 2}, {})
    assert res2.score == 1.0
    assert "modular" in res2.feedback.lower()


def test_structure_analyzer():
    analyzer = get_analyzer("static_analysis")
    student_src = Path("submissions/add_student.c")
    res = analyzer.analyze(student_src, None, {"max_cyclomatic": 8, "max_function_length": 40}, {})
    assert res.score == 0.60
    assert "single-block" in res.feedback


def test_readability_analyzer():
    analyzer = get_analyzer("llm_review")
    student_src = Path("submissions/add_student.c")
    res = analyzer.analyze(student_src, None, {"temperature": 0, "seed": 42}, {})
    assert res.score <= 0.70
    assert "single-letter" in res.feedback.lower() or "cramped" in res.feedback.lower()


def test_originality_analyzer():
    analyzer = get_analyzer("similarity_flag")
    target_src = Path("submissions/add_student.c")
    # Compare with corpus containing ref_solution
    res = analyzer.analyze(
        target_src, None, {"corpus_dir": "corpus/add/", "flag_threshold": 0.85}, {}
    )
    assert not res.raw_evidence["flagged"]
    assert res.score == 1.0

