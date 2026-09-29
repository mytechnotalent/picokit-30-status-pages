#!/usr/bin/env python3
"""Compile and execute the native unit test suite."""
import shutil
import subprocess
import sys
from pathlib import Path


def _find_compiler() -> str:
    """
    Locate host C compiler.

    Parameters
    ----------
    None

    Returns
    -------
    str
        Path or command name for host C compiler.
    """
    return shutil.which("clang") or shutil.which("gcc") or "cc"


def _owned_sources() -> list[str]:
    """
    Return owned module C source files.

    Parameters
    ----------
    None

    Returns
    -------
    list[str]
        Firmware module source path strings.
    """
    return [
        "firmware/src/crc.c",
        "firmware/src/radio.c",
        "firmware/src/status_led.c",
        "firmware/src/ir_remote.c",
        "firmware/src/button.c",
        "firmware/src/display.c",
        "firmware/src/aes.c",
        "firmware/src/ccm.c",
        "firmware/src/envelope.c",
        "firmware/src/monitor.c",
    ]


def _sources() -> list[str]:
    """
    Compose the full native test translation unit list.

    Parameters
    ----------
    None

    Returns
    -------
    list[str]
        Harness and adapter test source paths.
    """
    return [
        "firmware/tests/harness/harness.c",
        "firmware/tests/test_picokit_30_status_pages_and_security.c",
        "firmware/tests/test_peripheral_and_crypto.c",
    ]


def _include_flags() -> list[str]:
    """
    Compose compiler include flags.

    Parameters
    ----------
    None

    Returns
    -------
    list[str]
        Include flags for compilation.
    """
    return [
        "-Ifirmware/include",
        "-Ifirmware/tests",
        "-Ifirmware/tests/mock",
        "-Ifirmware/tests/harness",
    ]


def _compile_test_binary(out_bin: Path) -> int:
    """
    Compile test binary with host C compiler.

    Parameters
    ----------
    out_bin : pathlib.Path
        Output executable destination path.

    Returns
    -------
    int
        Compiler return code.
    """
    flags = ["-Wall", "-Wextra", "-O2", "-o", str(out_bin)]
    cmd = [_find_compiler()] + flags + _include_flags() + _sources()
    return subprocess.run(cmd).returncode


def _execute_test(out_bin: Path) -> int:
    """
    Execute compiled test binary.

    Parameters
    ----------
    out_bin : pathlib.Path
        Test executable path.

    Returns
    -------
    int
        Test process exit code.
    """
    return subprocess.run([str(out_bin)]).returncode


def main() -> int:
    """
    Build and execute test suite.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process return code.
    """
    out_dir = Path("build/test")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_bin = out_dir / "test_picokit_30_status_pages_and_security"
    rc = _compile_test_binary(out_bin)
    return _execute_test(out_bin) if rc == 0 else rc


if __name__ == "__main__":
    sys.exit(main())
