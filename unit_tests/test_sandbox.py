"""
Unit tests for ProcessSandbox execution, time limits, and crash survival.
"""

import sys
import tempfile
from pathlib import Path
from autograder.sandbox import ProcessSandbox
from autograder.compiler import CCompiler


def test_sandbox_normal_execution():
    compiler = CCompiler()
    sandbox = ProcessSandbox(default_timeout_s=2.0)
    
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "hello.c"
        exe = Path(tmp) / "hello.exe"
        src.write_text("""#include <stdio.h>
int main(void) {
    printf("HELLO_AUTOGRADER\\n");
    return 0;
}
""")
        cr = compiler.compile(src, exe)
        assert cr.success
        
        res = sandbox.run_binary(exe, timeout_s=2.0)
        assert res.returncode == 0
        assert "HELLO_AUTOGRADER" in res.stdout
        assert not res.timed_out
        assert not res.crashed


def test_sandbox_infinite_loop_timeout():
    compiler = CCompiler()
    sandbox = ProcessSandbox(default_timeout_s=1.0)
    
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "loop.c"
        exe = Path(tmp) / "loop.exe"
        src.write_text("""#include <stdio.h>
int main(void) {
    while(1) {}
    return 0;
}
""")
        cr = compiler.compile(src, exe)
        assert cr.success
        
        # Test hard timeout survival
        res = sandbox.run_binary(exe, timeout_s=0.5)
        assert res.timed_out
        assert "suspected infinite loop" in (res.crash_reason or "").lower()
