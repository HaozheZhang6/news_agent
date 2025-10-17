#!/usr/bin/env python3
"""
Thin wrapper to invoke the main VAD/Interruption runner from integration folder.
Location-agnostic: resolves project root and imports tools from there.
"""

import sys
from pathlib import Path


def main():
    script_dir = Path(__file__).parent
    project_root = (script_dir / ".." / "..").resolve()
    runner = project_root / "tests" / "run_vad_tests.py"
    if not runner.exists():
        print(f"Runner not found: {runner}")
        return 1

    # Re-exec python with the original runner and pass through args
    import subprocess

    cmd = [sys.executable, str(runner)] + sys.argv[1:]
    return subprocess.call(cmd, cwd=project_root)


if __name__ == "__main__":
    sys.exit(main())


