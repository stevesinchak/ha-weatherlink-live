"""Platinum `strict-typing`: the integration must pass mypy --strict (settings in mypy.ini)."""

import subprocess
import sys


def test_mypy_strict():
    # Separate process: compiled mypy loaded next to the HA test harness segfaults Python at exit
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--config-file", "mypy.ini"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
