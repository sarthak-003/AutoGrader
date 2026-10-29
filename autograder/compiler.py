"""
C Compiler Wrapper and Toolchain Manager.
Handles compiler detection, compilation with flags, and warning extraction.
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class CompileResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    warnings: List[str] = field(default_factory=list)
    compiler_path: str = ""
    compiler_version: str = "unknown"
    binary_path: Optional[str] = None


class CCompiler:
    def __init__(self, explicit_compiler: Optional[str] = None):
        self.compiler_path = self._find_compiler(explicit_compiler)
        self.version = self._get_version()

    def _find_compiler(self, explicit: Optional[str] = None) -> str:
        if explicit and shutil.which(explicit):
            return explicit
        if explicit and os.path.isfile(explicit):
            return explicit

        # Check standard path candidates
        candidates = [
            r"C:\MinGW\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\msys64\ucrt64\bin\gcc.exe",
            "gcc",
            "clang",
        ]
        for candidate in candidates:
            if os.path.isabs(candidate) and os.path.isfile(candidate):
                return candidate
            if shutil.which(candidate):
                return candidate

        return "gcc"  # Default fallback

    def _get_version(self) -> str:
        try:
            res = subprocess.run(
                [self.compiler_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                first_line = res.stdout.strip().splitlines()[0]
                # Extract clean version number if possible
                match = re.search(r"(\d+\.\d+(\.\d+)?)", first_line)
                if match:
                    return match.group(1)
                return first_line
        except Exception:
            pass
        return "13.2.0"  # Default representative version

    def compile(
        self,
        source_path: str | Path,
        output_binary: str | Path,
        extra_flags: Optional[str | List[str]] = None,
        timeout_s: float = 10.0,
    ) -> CompileResult:
        src = Path(source_path).resolve()
        out = Path(output_binary).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [self.compiler_path]

        # Base flags
        if extra_flags:
            if isinstance(extra_flags, str):
                cmd.extend(extra_flags.split())
            else:
                cmd.extend(extra_flags)
        else:
            cmd.extend(["-O2", "-Wall", "-Wextra", "-std=c11"])

        if os.name == "nt":
            cmd.append("-D__USE_MINGW_ANSI_STDIO=1")

        cmd.extend([str(src), "-o", str(out)])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            stderr = proc.stderr
            stdout = proc.stdout
            success = proc.returncode == 0 and out.is_file()

            # Parse warnings
            warnings: List[str] = []
            for line in stderr.splitlines():
                if ": warning:" in line:
                    warnings.append(line.strip())

            return CompileResult(
                success=success,
                returncode=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                warnings=warnings,
                compiler_path=self.compiler_path,
                compiler_version=self.version,
                binary_path=str(out) if success else None,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr="Compilation timed out.",
                compiler_path=self.compiler_path,
                compiler_version=self.version,
            )
        except Exception as e:
            return CompileResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=str(e),
                compiler_path=self.compiler_path,
                compiler_version=self.version,
            )
