"""
Originality and Similarity Analyzer (similarity_flag).
Flags suspected copying from online repositories, LLM templates, or peer submissions.
Utilizes token-normalized n-gram Winnowing and Jaccard similarity.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult


def tokenize_c_code(code: str) -> List[str]:
    """Tokenizes and normalizes C source code for structural similarity comparison."""
    # 1. Remove comments
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.DOTALL)
    code = re.sub(r"//.*", " ", code)

    # 2. Extract tokens
    tokens = re.findall(r"[a-zA-Z_]\w*|[0-9]+|[^\s\w]", code)

    # 3. Normalize variable identifiers while preserving keywords
    keywords = {
        "int", "char", "float", "double", "long", "short", "void", "unsigned", "signed",
        "struct", "union", "enum", "typedef", "sizeof", "return", "if", "else", "switch",
        "case", "default", "while", "do", "for", "break", "continue", "goto", "include",
        "main", "printf", "scanf", "puts", "getchar", "putchar", "malloc", "free"
    }

    normalized = []
    var_map: Dict[str, str] = {}
    var_counter = 0

    for tok in tokens:
        if tok in keywords:
            normalized.append(tok)
        elif re.match(r"^[0-9]+$", tok):
            normalized.append("NUM")
        elif re.match(r"^[a-zA-Z_]\w*$", tok):
            if tok not in var_map:
                var_counter += 1
                var_map[tok] = f"V{var_counter}"
            normalized.append(var_map[tok])
        else:
            normalized.append(tok)

    return normalized


def compute_ngrams(tokens: List[str], n: int = 4) -> Set[str]:
    """Computes set of n-gram shingles from tokens."""
    if len(tokens) < n:
        return {"_".join(tokens)}
    return {"_".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Computes Jaccard similarity coefficient between two token sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


@register_analyzer("similarity_flag")
class SimilarityFlagAnalyzer(BaseAnalyzer):
    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            target_code = f.read()

        corpus_dir_rel = params.get("corpus_dir", "submissions/")
        flag_threshold = float(params.get("flag_threshold", 0.85))

        corpus_dir = Path(corpus_dir_rel)
        if not corpus_dir.is_absolute():
            corpus_dir = (Path.cwd() / corpus_dir).resolve()

        target_tokens = tokenize_c_code(target_code)
        target_ngrams = compute_ngrams(target_tokens)

        max_sim = 0.0
        most_similar_file = None
        comparisons = []

        if corpus_dir.is_dir():
            for peer_file in corpus_dir.glob("*.c"):
                # Do not compare against self
                if peer_file.resolve() == source_path.resolve():
                    continue

                try:
                    with open(peer_file, "r", encoding="utf-8", errors="replace") as pf:
                        peer_code = pf.read()
                    peer_tokens = tokenize_c_code(peer_code)
                    peer_ngrams = compute_ngrams(peer_tokens)
                    sim = jaccard_similarity(target_ngrams, peer_ngrams)
                    comparisons.append({
                        "file": peer_file.name,
                        "similarity": round(sim, 3),
                    })
                    if sim > max_sim:
                        max_sim = sim
                        most_similar_file = peer_file.name
                except Exception:
                    pass

        flagged = max_sim >= flag_threshold
        # If flagged, score drops; if not flagged, full 1.0
        score = 0.0 if flagged else 1.0

        if flagged:
            feedback = f"max similarity {max_sim:.2f} with {most_similar_file} exceeds {flag_threshold:.2f} threshold (FLAGGED)"
            suggestions = ["Ensure independent authoring; do not replicate template code or peer submissions."]
        else:
            feedback = f"max similarity {max_sim:.2f}, not flagged"
            suggestions = []

        return AnalyzerResult(
            score=round(score, 2),
            raw_evidence={
                "corpus_dir": corpus_dir_rel,
                "flag_threshold": flag_threshold,
                "max_similarity": round(max_sim, 2),
                "flagged": flagged,
                "most_similar_file": most_similar_file,
                "comparisons": comparisons,
            },
            feedback=feedback,
            suggestions=suggestions,
        )

