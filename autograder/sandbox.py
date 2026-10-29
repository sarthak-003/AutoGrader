"""
Process Sandboxing and Safe Execution Supervisor.
Enforces strict execution timeouts and memory caps, safely intercepting crashes,
infinite loops, and memory overruns.
"""

from __future__ import annotations
import os
import sys
import time
import subprocess
import threading
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool
    memory_exceeded: bool
    crashed: bool
    crash_reason: Optional[str]
    duration_ms: float
    peak_memory_mb: float


class ProcessSandbox:
    """Supervises binary execution with time and memory boundaries."""

    def __init__(self, default_timeout_s: float = 1.0, default_memory_mb: int = 64):
        self.default_timeout_s = default_timeout_s
        self.default_memory_mb = default_memory_mb

    def run_binary(
        self,
        binary_path: str | Path,
        input_data: str = "",
        timeout_s: Optional[float] = None,
        memory_limit_mb: Optional[int] = None,
    ) -> ExecutionResult:
        binary_str = str(Path(binary_path).resolve())
        timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        mem_limit = memory_limit_mb if memory_limit_mb is not None else self.default_memory_mb

        start_time = time.perf_counter()
        proc = subprocess.Popen(
            [binary_str],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        timed_out = False
        memory_exceeded = False
        peak_memory_mb = 0.0
        monitor_stop = threading.Event()

        # Background thread to monitor memory usage
        def memory_monitor():
            nonlocal memory_exceeded, peak_memory_mb
            if psutil is None:
                return
            try:
                ps_proc = psutil.Process(proc.pid)
                while not monitor_stop.is_set() and proc.poll() is None:
                    try:
                        mem_bytes = ps_proc.memory_info().rss
                        mem_mb = mem_bytes / (1024 * 1024)
                        if mem_mb > peak_memory_mb:
                            peak_memory_mb = mem_mb
                        if mem_mb > mem_limit:
                            memory_exceeded = True
                            proc.kill()
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    time.sleep(0.01)
            except Exception:
                pass

        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()

        stdout_data, stderr_data = "", ""
        try:
            stdout_data, stderr_data = proc.communicate(input=input_data, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            # Kill process tree
            self._kill_process_tree(proc)
            try:
                stdout_data, stderr_data = proc.communicate(timeout=0.2)
            except Exception:
                pass
        finally:
            monitor_stop.set()
            monitor_thread.join(timeout=0.1)

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        returncode = proc.returncode if proc.returncode is not None else -1
        crashed = False
        crash_reason = None

        if timed_out:
            crash_reason = "Execution timed out (suspected infinite loop)"
        elif memory_exceeded:
            crash_reason = f"Memory limit exceeded (> {mem_limit} MB)"
        elif returncode != 0:
            crashed = True
            crash_reason = self._interpret_returncode(returncode)

        return ExecutionResult(
            stdout=stdout_data or "",
            stderr=stderr_data or "",
            returncode=returncode,
            timed_out=timed_out,
            memory_exceeded=memory_exceeded,
            crashed=crashed,
            crash_reason=crash_reason,
            duration_ms=duration_ms,
            peak_memory_mb=peak_memory_mb,
        )

    def _kill_process_tree(self, proc: subprocess.Popen):
        try:
            if psutil is not None:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
            else:
                proc.kill()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _interpret_returncode(self, code: int) -> str:
        # Common Windows NTSTATUS / signal codes
        if sys.platform == "win32":
            unsigned_code = code & 0xFFFFFFFF
            if unsigned_code == 0xC0000005:
                return "Access Violation (Segmentation Fault / Null Pointer Dereference)"
            if unsigned_code == 0xC0000094:
                return "Integer Division by Zero"
            if unsigned_code == 0xC00000FD:
                return "Stack Overflow (Infinite Recursion)"
            if unsigned_code == 0xC0000028:
                return "Bad Stack"
            if unsigned_code == 0xC0000409:
                return "Security Check Failure (Buffer Overrun detected)"
        # POSIX signals
        if code == -11:
            return "Segmentation Fault (SIGSEGV)"
        if code == -8:
            return "Floating Point Exception (SIGFPE)"
        if code == -6:
            return "Aborted (SIGABRT)"
        if code == -9:
            return "Killed (SIGKILL)"
        return f"Process terminated abnormally with exit code {code}"

