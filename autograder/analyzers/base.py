"""
Base Analyzer Interface and Registry for AutoGrader.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Type
from autograder.config import AnalyzerResult


class BaseAnalyzer(ABC):
    """Abstract base class for all expert grading analyzers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        """
        Executes analysis on the submission.
        
        Args:
            source_path: Path to the student's .c source code.
            binary_path: Path to compiled binary (if available).
            params: Rule parameters slice specific to this analyzer.
            context: Shared grading context (compiler info, sandbox instance, etc.)
            
        Returns:
            AnalyzerResult with normalized score (0.0 - 1.0), raw evidence, and feedback.
        """
        pass


ANALYZER_REGISTRY: Dict[str, Type[BaseAnalyzer]] = {}


def register_analyzer(name: str):
    """Decorator to register an analyzer implementation."""
    def decorator(cls: Type[BaseAnalyzer]):
        ANALYZER_REGISTRY[name] = cls
        return cls
    return decorator


def get_analyzer(name: str) -> BaseAnalyzer:
    """Retrieves an instantiated analyzer by registered name."""
    if name not in ANALYZER_REGISTRY:
        raise KeyError(
            f"Unknown analyzer '{name}'. Available analyzers: {list(ANALYZER_REGISTRY.keys())}"
        )
    return ANALYZER_REGISTRY[name](name=name)

