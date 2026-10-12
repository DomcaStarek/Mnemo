"""Command runner utility for safely executing shell snippets."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Represents the outcome of a command execution."""

    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    cancelled: bool = False


class CommandRunner:
    """Executes shell commands in a background thread with cancellation support."""

    def __init__(self) -> None:
        self._current_process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._is_cancelled = False

    def cancel(self) -> None:
        """Cancel the currently running command."""
        with self._lock:
            self._is_cancelled = True
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                    # On Windows, force kill if still alive
                    if sys.platform == "win32":
                        self._current_process.kill()
                except Exception:
                    pass

    def run(
        self,
        command: str,
        cwd: str | None = None,
        shell_type: str = "powershell",
        timeout: float | None = 60.0,
        on_output: Callable[[str], None] | None = None,
    ) -> ExecutionResult:
        """Run a command synchronously (call from worker thread).

        Parameters:
            command: Shell command string.
            cwd: Working directory (defaults to current dir).
            shell_type: 'powershell', 'cmd', or 'default'.
            timeout: Maximum seconds to allow running.
            on_output: Callback for line-by-line output streaming.
        """
        self._is_cancelled = False
        start_time = time.perf_counter()
        target_cwd = cwd or os.getcwd()

        if sys.platform == "win32":
            if shell_type.lower() == "powershell":
                args = [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ]
            elif shell_type.lower() == "cmd":
                args = ["cmd.exe", "/c", command]
            else:
                args = command
        else:
            args = ["/bin/sh", "-c", command]

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        timed_out = False

        try:
            with self._lock:
                self._current_process = subprocess.Popen(
                    args,
                    cwd=target_cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    shell=isinstance(args, str),
                )

            # Read stdout and stderr concurrently
            def read_pipe(pipe, chunk_list, is_err=False):
                try:
                    for line in iter(pipe.readline, ""):
                        chunk_list.append(line)
                        if on_output:
                            prefix = "[ERR] " if is_err else ""
                            on_output(f"{prefix}{line}")
                finally:
                    pipe.close()

            t_out = threading.Thread(
                target=read_pipe,
                args=(self._current_process.stdout, stdout_chunks, False),
                daemon=True,
            )
            t_err = threading.Thread(
                target=read_pipe,
                args=(self._current_process.stderr, stderr_chunks, True),
                daemon=True,
            )

            t_out.start()
            t_err.start()

            # Wait for process with timeout
            try:
                self._current_process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                self.cancel()

            t_out.join(timeout=2.0)
            t_err.join(timeout=2.0)

            returncode = (
                self._current_process.returncode if self._current_process else -1
            )

        except Exception as e:
            stderr_chunks.append(f"Execution error: {e}\n")
            returncode = -1

        duration = time.perf_counter() - start_time
        return ExecutionResult(
            command=command,
            returncode=returncode,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            duration_seconds=duration,
            timed_out=timed_out,
            cancelled=self._is_cancelled,
        )
