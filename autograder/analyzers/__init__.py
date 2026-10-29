"""
Analyzers package for AutoGrader.
Automatically registers all available expert analyzers.
"""

from autograder.analyzers.base import (
    BaseAnalyzer,
    ANALYZER_REGISTRY,
    register_analyzer,
    get_analyzer,
)
from autograder.analyzers.correctness import IOTestAnalyzer
from autograder.analyzers.syntax import CompilerWarningsAnalyzer
from autograder.analyzers.structure import StaticAnalysisAnalyzer
from autograder.analyzers.modularity import FunctionSplitAnalyzer
from autograder.analyzers.logical import EdgeCaseRunnerAnalyzer
from autograder.analyzers.complexity import ComplexityEstimatorAnalyzer
from autograder.analyzers.memory_safety import SanitizerRunAnalyzer
from autograder.analyzers.readability import LLMReviewAnalyzer
from autograder.analyzers.originality import SimilarityFlagAnalyzer

__all__ = [
    "BaseAnalyzer",
    "ANALYZER_REGISTRY",
    "register_analyzer",
    "get_analyzer",
    "IOTestAnalyzer",
    "CompilerWarningsAnalyzer",
    "StaticAnalysisAnalyzer",
    "FunctionSplitAnalyzer",
    "EdgeCaseRunnerAnalyzer",
    "ComplexityEstimatorAnalyzer",
    "SanitizerRunAnalyzer",
    "LLMReviewAnalyzer",
    "SimilarityFlagAnalyzer",
]

