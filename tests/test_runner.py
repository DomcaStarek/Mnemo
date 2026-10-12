"""Tests for command runner execution."""

from mnemo.runner import CommandRunner


def test_command_runner_echo():
    runner = CommandRunner()
    output_lines = []

    def on_out(line):
        output_lines.append(line)

    res = runner.run(
        "Write-Output 'Hello Mnemo'", shell_type="powershell", on_output=on_out
    )
    assert res.returncode == 0
    assert "Hello Mnemo" in res.stdout
    assert not res.timed_out
    assert not res.cancelled
    assert res.duration_seconds >= 0.0
