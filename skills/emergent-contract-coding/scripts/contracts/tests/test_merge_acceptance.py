"""Merge acceptance fixture (issue #27): a textual-clean registry merge that
is semantically wrong must be caught, and regeneration must be the fix.

Scenario (issue #27 acceptance): one branch removes a usage record (deletes
extra.py); the other touches the interface (re-points extra.py's call from
helpers.save to pkg.api:api_create). The sources hit a delete/modify
conflict, but the registry merges CLEANLY — and the merged registry is then
semantically wrong. The post-merge registry must equal `contracts generate`
over the merged tree, with the divergence diff surfaced, never silently
accepted.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CONFIG = """\
[source]
tree = ["src"]

[inputs]
patterns = ["pkg.api:api_*", "helpers:save"]

[rigid]
patterns = ["pkg.api:api_*", "ext:*"]
"""

BASE_EXTRA = """\
import helpers


def use():
    return helpers.save(2)
"""

LEFT_EXTRA = """\
from pkg.api import api_create


def use():
    return api_create(2)
"""


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class TestMergeAcceptance(unittest.TestCase):
    """End-to-end merge fixture on a real git repo, via the CLI only."""

    def run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "contracts", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    q for q in (str(REPO_ROOT), os.environ.get("PYTHONPATH", "")) if q
                ),
            },
        )

    def git(self, root: Path, *argv: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        return subprocess.run(["git", *argv], cwd=root, check=check, env=env,
                              text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "contracts.toml").write_text(CONFIG, encoding="utf-8")
        _write(self.root, "src/pkg/__init__.py", "")
        _write(self.root, "src/pkg/api.py", "def api_create(x):\n    return x\n")
        _write(self.root, "src/helpers.py", "def save(x):\n    return x\n")
        _write(self.root, "src/app.py",
               "from pkg.api import api_create\n\n\ndef run():\n"
               "    return api_create(1)\n")
        _write(self.root, "src/extra.py", BASE_EXTRA)
        self.git(self.root, "init", "-q")
        self.assertEqual(self.run_cli(self.root, "generate").returncode, 0)
        self.git(self.root, "add", "-A")
        self.git(self.root, "commit", "-qm", "base")

    def test_textual_clean_merge_is_semantically_wrong_and_regenerate_fixes_it(self):
        root = self.root

        # Left branch: touch the interface — extra.py re-points its call
        # from helpers.save to pkg.api:api_create.
        self.git(root, "checkout", "-qb", "left")
        _write(root, "src/extra.py", LEFT_EXTRA)
        self.assertEqual(self.run_cli(root, "generate").returncode, 0)
        self.git(root, "commit", "-qam", "left: extra.py calls api_create")

        # Main branch: remove the usage record — delete extra.py entirely.
        self.git(root, "checkout", "-q", "main")
        self.git(root, "rm", "-q", "src/extra.py")
        self.assertEqual(self.run_cli(root, "generate").returncode, 0)
        self.git(root, "commit", "-qam", "main: remove extra.py usage record")

        # Merge: the registry file merges cleanly (no conflict marker in it),
        # while the sources hit a delete/modify conflict.
        merge = self.git(root, "merge", "left", "-m", "merge", check=False)
        self.assertNotEqual(merge.returncode, 0, merge.stdout + merge.stderr)
        status = self.git(root, "status", "--porcelain").stdout
        self.assertTrue(
            any(ln.endswith("src/extra.py") and ln[:2] in {"DU", "UD", "UU"}
                for ln in status.splitlines()),
            f"expected a delete/modify conflict on the source file, got: {status!r}")
        reg_status = [ln for ln in status.splitlines()
                      if ln.split(None, 1)[-1].endswith("registry.md")]
        self.assertTrue(all(ln[0] in "M " and ln[1] in "M " for ln in reg_status),
                        f"registry must merge cleanly, got: {reg_status!r}")
        self.assertNotIn("<<<<<<<", (root / "registry.md").read_text(encoding="utf-8"))

        # Resolve the source conflict by taking the deletion. The textual
        # merge result is now in the tree: clean, and semantically wrong.
        self.git(root, "rm", "-q", "src/extra.py")
        self.git(root, "commit", "-qm", "merge: drop extra.py")
        merged_registry = (root / "registry.md").read_text(encoding="utf-8")
        self.assertIn("- src/extra.py:use", merged_registry,
                      "the textually merged registry carries the stale bullet")

        # The mechanical merge result is rejected by check, naming the site.
        check = self.run_cli(root, "check")
        self.assertNotEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("src/extra.py:use", check.stdout)

        # Regeneration is the fix: it diverges from the merged registry
        # (that diff is the co-change/loss report the agent must surface),
        # and after it the merge goes green.
        self.assertEqual(self.run_cli(root, "generate").returncode, 0)
        regenerated = (root / "registry.md").read_text(encoding="utf-8")
        self.assertNotIn("- src/extra.py:use", regenerated)
        self.assertNotEqual(regenerated, merged_registry, "divergence diff non-empty")
        self.assertEqual(self.run_cli(root, "check").returncode, 0)
        self.assertEqual(self.run_cli(root, "log", "check").returncode, 0)


if __name__ == "__main__":
    unittest.main()
