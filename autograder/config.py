"""
AutoGrader Configuration and Rules Schema.
Defines the external rule set format, metric definitions, and report structures.
"""

from __future__ import annotations
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class MetricRule:
    name: str
    analyzer: str
    weight: float
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GradingRules:
    problem: str
    time_limit_s: float = 1.0
    memory_limit_mb: int = 64
    metrics: List[MetricRule] = field(default_factory=list)
    raw_content: str = ""
    rules_hash: str = ""

    @classmethod
    def load_from_file(cls, filepath: str | Path) -> GradingRules:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Grading rules file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        rules_hash = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
        data = json.loads(content)

        metrics: List[MetricRule] = []
        for m in data.get("metrics", []):
            metrics.append(
                MetricRule(
                    name=m["name"],
                    analyzer=m["analyzer"],
                    weight=float(m["weight"]),
                    params=m.get("params", {}),
                )
            )

        # Validate weights sum
        total_weight = sum(m.weight for m in metrics)
        if abs(total_weight - 1.0) > 1e-4:
            raise ValueError(
                f"Metric weights must sum to 1.00 (got {total_weight:.4f})"
            )

        return cls(
            problem=data.get("problem", "unknown"),
            time_limit_s=float(data.get("time_limit_s", 1.0)),
            memory_limit_mb=int(data.get("memory_limit_mb", 64)),
            metrics=metrics,
            raw_content=content,
            rules_hash=rules_hash,
        )


@dataclass
class AnalyzerResult:
    score: float  # Normalized 0.0 to 1.0
    raw_evidence: Dict[str, Any]
    feedback: str
    failing_cases: List[Dict[str, Any]] = field(default_factory=list)
    counter_cases: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class FirstPassResult:
    compiled: bool
    smoke_ok: bool
    suspected_infinite_loop: bool
    static_sanity_ok: bool
    details: Dict[str, Any] = field(default_factory=dict)

