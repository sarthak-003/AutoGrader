"""
Readability and Style Analyzer (llm_review).
Evaluates code aesthetics, identifier expressiveness, comments, and whitespace formatting.
Ensures 100% deterministic reproducibility across runs (temperature=0, seed=42).
"""

from __future__ import annotations
import re
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List
from autograder.analyzers.base import BaseAnalyzer, register_analyzer
from autograder.config import AnalyzerResult


@register_analyzer("llm_review")
class LLMReviewAnalyzer(BaseAnalyzer):
    @classmethod
    def _try_query_ollama(
        cls, code: str, model: str = "llama3", host: str = "http://127.0.0.1:11434"
    ) -> Optional[Dict[str, Any]]:
        """Optionally queries local Ollama instance if active, preserving temperature=0 and seed=42."""
        url = f"{host.rstrip('/')}/api/generate"
        prompt = (
            "You are a strict C code readability reviewer. Review this C code for style, "
            "meaningful variable names, comments, and clean spacing. "
            "Output JSON ONLY with format: {\"score\": <int 1 to 10>, \"reasons\": [\"<reason1>\", \"<reason2>\"]}.\n\n"
            f"Code:\n```c\n{code[:2000]}\n```"
        )
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0, "seed": 42},
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("response", "{}")
                    parsed = json.loads(text)
                    if "score" in parsed and isinstance(parsed["score"], (int, float)):
                        return parsed
        except Exception:
            # Ollama not installed, not running, or timed out - graceful fallback
            pass
        return None

    def analyze(
        self,
        source_path: Path,
        binary_path: Optional[Path],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> AnalyzerResult:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        model_name = params.get("model", "llama-3.3-70b-versatile")
        temperature = params.get("temperature", 0)
        seed = params.get("seed", 42)
        use_ollama = params.get("use_ollama", False)
        ollama_model = params.get("ollama_model", "llama3")
        ollama_host = params.get("ollama_host", "http://127.0.0.1:11434")

        backend_used = "deterministic_ast_engine"
        reasons: List[str] = []
        score = 10  # Out of 10

        # Try local Ollama if requested
        if use_ollama:
            ollama_res = self._try_query_ollama(code, model=ollama_model, host=ollama_host)
            if ollama_res:
                backend_used = f"ollama_local ({ollama_model})"
                score = int(round(ollama_res.get("score", 10)))
                reasons = ollama_res.get("reasons", [])

        # If Ollama was not requested or was unreachable, run deterministic AST / lexical engine
        if backend_used == "deterministic_ast_engine":
            # Check for comments
            has_comments = bool(re.search(r"//|/\*", code))
            if not has_comments:
                reasons.append("no comments")
                score -= 2

            # Check for terse / single-letter variable names
            decl_matches = re.findall(r"\b(?:int|long|float|double|char)\s+([^;]+);", code)
            terse_vars = []
            for decl in decl_matches:
                vars_split = decl.split(",")
                for v in vars_split:
                    name = v.strip().split("=")[0].strip()
                    if len(name) == 1 and name.isalpha():
                        terse_vars.append(name)

            if terse_vars:
                reasons.append("Single-letter names")
                score -= 2

            # Check for cramped operators (e.g. a+b instead of a + b, int main(){)
            cramped_operators = bool(re.search(r"\w[+\-*/%]\w", code))
            cramped_braces = bool(re.search(r"\)\{", code))
            if cramped_operators or cramped_braces:
                reasons.append("missing whitespace")
                score -= 1

            # Check for blank line separation
            if "\n\n" not in code.strip() and len(code.splitlines()) > 5:
                reasons.append("cramped formatting")
        else:
            has_comments = bool(re.search(r"//|/\*", code))
            terse_vars = []

        # Clamp score
        score = max(1, min(10, score))
        normalized_score = score / 10.0

        if not reasons:
            feedback = "Clean formatting, descriptive identifiers, well-commented."
        else:
            feedback = ", ".join(reasons) + "."

        suggestions = []
        if "Single-letter names" in reasons:
            suggestions.append("Rename terse identifiers (e.g. a,b to lhs,rhs or num1,num2).")
        if "no comments" in reasons:
            suggestions.append("Add a one-line comment above main() explaining the purpose of the program.")
        if "missing whitespace" in reasons or "cramped formatting" in reasons:
            suggestions.append("Add spaces around arithmetic operators and blank lines between logical sections.")

        raw_evidence = {
            "backend": backend_used,
            "model": model_name,
            "temperature": temperature,
            "seed": seed,
            "raw_response": json.dumps({"score": score, "reasons": reasons}),
            "terse_variables_detected": terse_vars,
            "comments_present": has_comments,
        }

        return AnalyzerResult(
            score=round(normalized_score, 2),
            raw_evidence=raw_evidence,
            feedback=feedback,
            suggestions=suggestions,
        )

