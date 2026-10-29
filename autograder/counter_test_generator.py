"""
Counter-Test Case and Corner-Case Generator.
Generates adversarial test inputs, edge cases, and explains failure mechanisms.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple


class CounterTestGenerator:
    """Synthesizes boundary inputs and counter test cases for C programs."""

    INT32_MAX = 2147483647
    INT32_MIN = -2147483648

    @classmethod
    def generate_corner_cases_for_two_integers() -> List[Tuple[str, str, str]]:
        """
        Returns list of (input_str, expected_output_str, corner_description)
        """
        return [
            ("0 0\n", "0\n", "Identity element zero addition"),
            ("-5 0\n", "-5\n", "Negative with zero"),
            ("0 42\n", "42\n", "Zero with positive"),
            ("-15 -25\n", "-40\n", "Two negative numbers"),
            ("100 -50\n", "50\n", "Positive and negative yielding positive"),
            ("-100 50\n", "-50\n", "Positive and negative yielding negative"),
            ("2147483646 1\n", "2147483647\n", "Boundary reaching INT_MAX exactly"),
            ("-2147483647 -1\n", "-2147483648\n", "Boundary reaching INT_MIN exactly"),
            ("2147483647 1\n", "2147483648\n", "Overflow exceeding INT_MAX by 1"),
            ("-2147483648 -1\n", "-2147483649\n", "Underflow below INT_MIN by 1"),
            ("  7    5  \n", "12\n", "Leading and multiple internal whitespace characters"),
            ("2147483647 2147483647\n", "4294967294\n", "Max positive addition"),
        ]

    @classmethod
    def explain_failure(cls, input_str: str, got_output: str, expected_output: str) -> str:
        """Generates an insightful engineering explanation of why a test failed."""
        parts = input_str.strip().split()
        if len(parts) == 2:
            try:
                a, b = int(parts[0]), int(parts[1])
                true_sum = a + b
                # Check 32-bit signed overflow
                if true_sum > cls.INT32_MAX or true_sum < cls.INT32_MIN:
                    return (
                        f"a + b overflows on 32-bit signed ints. Use long long or "
                        f"check that b <= INT_MAX - a before adding."
                    )
                if not got_output.strip() and expected_output.strip():
                    return "Submission produced no output or crashed before flushing stdout."
                if got_output.strip() != expected_output.strip():
                    return f"Numerical discrepancy: calculated {got_output.strip()} instead of expected {expected_output.strip()}."
            except ValueError:
                pass

        # Check two-sum / index search patterns
        if "target" in input_str.lower() or len(parts) > 2:
            if expected_output.strip() == "-1" and got_output.strip() != "-1":
                return "Failed to handle case where no valid elements or pairs satisfy the condition; expected -1."
            if got_output.strip() == "-1" and expected_output.strip() != "-1":
                return f"Did not find existing solution in array; expected indices '{expected_output.strip()}'."

        # Check boolean YES / NO or palindrome
        exp_upper = expected_output.strip().upper()
        got_upper = got_output.strip().upper()
        if exp_upper in ("YES", "NO") and got_upper in ("YES", "NO"):
            return f"Logic inverted: program output '{got_upper}', but input condition required '{exp_upper}'."

        if not got_output.strip():
            return "Program exited without producing any output or encountered an abnormal runtime termination (e.g. segfault / out of bounds)."
        if got_output.strip() == expected_output.strip():
            return "Output matched partially, but process was terminated by sandbox due to exceeding time/memory limits."
        return f"Output mismatch: got '{got_output.strip()}', expected '{expected_output.strip()}'."

