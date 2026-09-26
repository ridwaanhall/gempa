"""Repository hygiene: every app source file must be committable.

Regression guard: an unanchored `lib/` rule in .gitignore once silently excluded
app/static/js/lib/, so production served pages whose JS modules all 404'd.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="needs git")
def test_no_app_source_is_gitignored():
    files = [
        str(p.relative_to(ROOT).as_posix())
        for p in (ROOT / "app").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    result = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        input="\n".join(files),
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    ignored = [line for line in result.stdout.splitlines() if line.strip()]
    assert ignored == [], f"app files ignored by .gitignore: {ignored}"
