#!/usr/bin/env python3
"""Clean-venv pre-flight: reproduce CI's environment LOCALLY before pushing.

Why this exists
---------------
A normal `pytest` run uses your DEV environment, which silently differs from CI:
  * editable / older PINNED deps  (e.g. dazzle-filekit 0.3.1 locally vs the
    0.3.2 that CI resolves from `>=0.3.0`), and
  * AMBIENT packages that happen to be installed (e.g. pytest-asyncio) but are
    NOT declared in the `[dev]` extra, so CI does not have them.

CI does a fresh `pip install -e ".[dev]"` in a clean runner, which (a) resolves
every `>=` dependency to the LATEST on PyPI and (b) installs ONLY what the
package declares. This script mirrors that exactly: throwaway venv -> editable
install with the [dev] extra -> pytest. If this is green, CI's "Run tests" step
on the same Python version will be too.

Usage:  python tests/one-offs/preflight_clean_venv.py
Exit code is pytest's, so it can gate a pre-push hook.

NOTE: the venv lives in a temp dir and is a truly-throwaway runtime artifact,
so it is removed with shutil.rmtree (not safedel) on exit.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # tests/one-offs/ -> repo root


def _run(cmd, **kw):
    print(f"\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    return subprocess.run(cmd, **kw)


def main() -> int:
    work = tempfile.mkdtemp(prefix="fdf-preflight-")
    venv_dir = Path(work) / "venv"
    try:
        print(f"[preflight] python {sys.version.split()[0]}  repo={REPO}")
        venv.create(venv_dir, with_pip=True)
        bindir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        py = bindir / ("python.exe" if os.name == "nt" else "python")

        if _run([py, "-m", "pip", "install", "-q", "--upgrade", "pip"]).returncode:
            print("[preflight] FAILED: pip upgrade")
            return 2

        # Mirror CI's install command exactly (main.yml: pip install -e ".[dev]").
        if _run([py, "-m", "pip", "install", "-e", ".[dev]"], cwd=REPO).returncode:
            print("[preflight] FAILED: dependency install (this is itself a CI signal)")
            return 2

        # Surface the resolved versions -- the whole point is to see what CI sees.
        _run([py, "-m", "pip", "show", "dazzle-filekit", "dazzletreelib",
              "dazzle-lib", "pytest-asyncio"])

        # Run the suite the way CI does.
        rc = _run([py, "-m", "pytest", "tests", "-q", "--tb=short"], cwd=REPO).returncode
        banner = "GREEN -- safe to push" if rc == 0 else f"RED (pytest rc={rc}) -- DO NOT push"
        print(f"\n[preflight] {banner}")
        return rc
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
