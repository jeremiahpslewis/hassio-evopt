"""Exercise real Git histories locally; only the GitHub PR API is mocked."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "sync_upstream", Path(__file__).resolve().parents[1] / "scripts/sync_addon_upstream.py"
)
sync_upstream = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_upstream)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.upstream = self.root / "upstream.git"
        self.origin = self.root / "fork.git"
        self.author = self.root / "author"
        self.checkout = self.root / "checkout"
        for bare in (self.upstream, self.origin):
            self.git(self.root, "init", "--bare", "--initial-branch=main", str(bare))
        self.git(self.root, "init", "--initial-branch=main", str(self.author))
        self.identity(self.author)
        self.commit({"addon.txt": "base\n", ".github/keepalive": "base timestamp\n",
                     ".github/workflows/update-docker_tag.yml": "old updater\n"})
        self.git(self.author, "remote", "add", "upstream", str(self.upstream))
        self.git(self.author, "remote", "add", "origin", str(self.origin))
        for remote in ("origin", "upstream"):
            self.git(self.author, "push", remote, "main")
        self.git(self.root, "clone", str(self.origin), str(self.checkout))
        self.identity(self.checkout)
        self.old_cwd = Path.cwd()
        os.chdir(self.checkout)
        self.addCleanup(os.chdir, self.old_cwd)
        self.pulls = []
        self.created = 0
        self.mock = patch.object(sync_upstream, "gh", side_effect=self.gh)
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def git(self, cwd, *args):
        result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def identity(self, cwd):
        self.git(cwd, "config", "user.name", "Sync test")
        self.git(cwd, "config", "user.email", "sync@example.invalid")

    def commit(self, files, cwd=None):
        cwd = cwd or self.author
        for name, content in files.items():
            path = cwd / name
            if content is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        self.git(cwd, "add", "-A")
        self.git(cwd, "commit", "-m", "Fixture change")
        return self.git(cwd, "rev-parse", "HEAD")

    def gh(self, *args):
        if args[:2] == ("pr", "list"):
            return json.dumps(self.pulls)
        self.assertEqual(args[:2], ("pr", "create"))
        body = Path(args[args.index("--body-file") + 1]).read_text()
        self.assertIn("Create a merge commit", body)
        self.created += 1
        self.pulls = [{"number": self.created, "url": f"https://example.invalid/pull/{self.created}"}]
        return self.pulls[0]["url"]

    def sync(self):
        return sync_upstream.sync("example/fork", upstream=str(self.upstream))

    def fork_change(self, files):
        self.git(self.checkout, "switch", "main")
        sha = self.commit(files, self.checkout)
        self.git(self.checkout, "push", "origin", "main")
        return sha

    def upstream_change(self, files):
        sha = self.commit(files)
        self.git(self.author, "push", "upstream", "main")
        return sha

    def remote_sha(self, branch):
        return self.git(self.origin, "rev-parse", branch)

    def test_current_fork_only_updates_mirror(self):
        result = self.sync()
        self.assertIn("already contains", result)
        self.assertEqual(self.remote_sha(sync_upstream.MIRROR), self.remote_sha("main"))
        self.assertEqual(self.created, 0)

    def test_merge_preserves_fork_and_resolves_only_known_conflicts(self):
        fork_sha = self.fork_change({".github/keepalive": "fork timestamp\n",
                                    ".github/workflows/update-docker_tag.yml": None,
                                    ".github/workflows/build-optimizer.yml": "GHCR\n",
                                    "evopt/Dockerfile": "ENV OPTIMIZER_SOLVER=highs\n"})
        upstream_sha = self.upstream_change({".github/keepalive": "parent timestamp\n",
                                            ".github/workflows/update-docker_tag.yml": "updated legacy job\n",
                                            "upstream.txt": "new feature\n"})
        self.sync()
        self.assertEqual(self.remote_sha("main"), fork_sha)
        self.assertEqual(self.remote_sha(sync_upstream.MIRROR), upstream_sha)
        self.assertTrue(sync_upstream.ancestor(fork_sha, "HEAD"))
        self.assertTrue(sync_upstream.ancestor(upstream_sha, "HEAD"))
        self.assertFalse(Path(".github/workflows/update-docker_tag.yml").exists())
        self.assertEqual(Path(".github/keepalive").read_text(), "fork timestamp\n")
        self.assertIn("highs", Path("evopt/Dockerfile").read_text())
        self.assertEqual(Path("upstream.txt").read_text(), "new feature\n")

    def test_refresh_preserves_pr_edits_and_new_fork_commits(self):
        self.upstream_change({"upstream.txt": "first\n"})
        self.sync()
        manual_sha = self.commit({"manual.txt": "review fix\n"}, self.checkout)
        self.git(self.checkout, "push", "origin", f"HEAD:refs/heads/{sync_upstream.BRANCH}")
        fork_sha = self.fork_change({"fork.txt": "new customization\n"})
        upstream_sha = self.upstream_change({"upstream.txt": "second\n"})
        self.sync()
        for sha in (manual_sha, fork_sha, upstream_sha):
            self.assertTrue(sync_upstream.ancestor(sha, "HEAD"))
        self.assertEqual(self.created, 1)
        previous = self.remote_sha(sync_upstream.BRANCH)
        self.sync()
        self.assertEqual(self.remote_sha(sync_upstream.BRANCH), previous)
        self.assertEqual(self.created, 1)

    def test_unexpected_conflict_does_not_push_pr_branch(self):
        fork_sha = self.fork_change({"addon.txt": "fork behavior\n"})
        self.upstream_change({"addon.txt": "different upstream behavior\n"})
        with self.assertRaisesRegex(RuntimeError, "Manual conflict resolution required"):
            self.sync()
        self.assertEqual(self.remote_sha("main"), fork_sha)
        self.assertFalse(sync_upstream.exists(f"refs/remotes/origin/{sync_upstream.BRANCH}"))
        self.assertFalse(sync_upstream.exists("MERGE_HEAD"))
        self.assertEqual(sync_upstream.git("status", "--porcelain"), "")
        self.assertEqual(self.created, 0)

    def test_closed_unmerged_pr_is_not_overwritten(self):
        self.upstream_change({"upstream.txt": "first\n"})
        self.sync()
        previous = self.remote_sha(sync_upstream.BRANCH)
        self.pulls = []
        self.upstream_change({"upstream.txt": "second\n"})
        with self.assertRaisesRegex(RuntimeError, "unmerged work"):
            self.sync()
        self.assertEqual(self.remote_sha(sync_upstream.BRANCH), previous)

    def test_next_sync_after_merge_creates_new_pr(self):
        self.upstream_change({"upstream.txt": "first\n"})
        self.sync()
        previous = self.remote_sha(sync_upstream.BRANCH)
        self.git(self.checkout, "push", "origin", "HEAD:refs/heads/main")
        self.pulls = []
        self.upstream_change({"upstream.txt": "second\n"})
        self.sync()
        self.assertTrue(sync_upstream.ancestor(previous, "HEAD"))
        self.assertEqual(self.created, 2)

    def test_rewritten_upstream_does_not_overwrite_mirror(self):
        self.upstream_change({"upstream.txt": "first\n"})
        self.sync()
        mirror = self.remote_sha(sync_upstream.MIRROR)
        branch = self.remote_sha(sync_upstream.BRANCH)
        self.git(self.author, "reset", "--hard", "HEAD^")
        self.commit({"upstream.txt": "rewritten\n"})
        self.git(self.author, "push", "--force", "upstream", "main")
        with self.assertRaises(RuntimeError):
            self.sync()
        self.assertEqual(self.remote_sha(sync_upstream.MIRROR), mirror)
        self.assertEqual(self.remote_sha(sync_upstream.BRANCH), branch)


if __name__ == "__main__":
    unittest.main()
