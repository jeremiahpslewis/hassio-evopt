#!/usr/bin/env python3
"""Mirror the add-on parent and merge it into a reviewable branch without force pushes."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


UPSTREAM = "https://github.com/thecem/hassio-evopt.git"
MIRROR = "upstream/thecem-main"
BRANCH = "sync/addon-upstream"


def run(*args, check=True):
    result = subprocess.run(args, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def git(*args):
    return run("git", *args).stdout.strip()


def gh(*args):
    return run("gh", *args).stdout.strip()


def exists(ref):
    return run("git", "cat-file", "-e", ref, check=False).returncode == 0


def ancestor(base, head):
    result = run("git", "merge-base", "--is-ancestor", base, head, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip())
    return result.returncode == 0


def merge(ref):
    result = run("git", "merge", "--no-ff", "--no-commit", ref, check=False)
    if result.returncode and not exists("MERGE_HEAD"):
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    for path in git("diff", "--name-only", "--diff-filter=U").splitlines():
        if path == ".github/keepalive":
            # Both repositories write this timestamp; retain the fork's copy.
            if exists(f"HEAD:{path}"):
                git("checkout", "--ours", "--", path)
                git("add", "--", path)
            else:
                git("rm", "--", path)
        elif (path == ".github/workflows/update-docker_tag.yml"
              and not exists(f"HEAD:{path}")
              and exists("HEAD:.github/workflows/build-optimizer.yml")):
            # The fork replaced this Docker Hub updater with its GHCR builder.
            git("rm", "--", path)

    conflicts = git("diff", "--name-only", "--diff-filter=U")
    if conflicts:
        git("merge", "--abort")
        raise RuntimeError(f"Manual conflict resolution required; PR branch was not pushed:\n{conflicts}")
    if exists("MERGE_HEAD"):
        git("commit", "--no-edit")


def sync(repository, base="main", upstream=UPSTREAM):
    if git("status", "--porcelain"):
        raise RuntimeError("Run from a clean checkout.")
    git("check-ref-format", "--branch", base)
    git("fetch", "--prune", "--no-tags", "origin")
    upstream_ref = "refs/remotes/addon-upstream/main"
    git("fetch", "--no-tags", upstream, f"refs/heads/main:{upstream_ref}")
    upstream_sha = git("rev-parse", upstream_ref)
    # A rewritten upstream must be reviewed instead of silently replacing history.
    git("push", "origin", f"{upstream_sha}:refs/heads/{MIRROR}")
    base_ref = f"refs/remotes/origin/{base}"
    if ancestor(upstream_sha, base_ref):
        return f"{base} already contains {upstream_sha}; upstream mirror is current."

    pulls = json.loads(gh("pr", "list", "--repo", repository, "--state", "open",
                          "--base", base, "--head", BRANCH, "--json", "number,url"))
    branch_ref = f"refs/remotes/origin/{BRANCH}"
    if exists(branch_ref) and not pulls and not ancestor(branch_ref, base_ref):
        raise RuntimeError(
            f"{BRANCH} contains unmerged work but has no open PR. Reopen its PR or "
            "preserve/rename the branch before retrying. Nothing was overwritten."
        )
    git("switch", "--detach", branch_ref if pulls else base_ref)
    # Keep edits made on the open PR and incorporate newer fork commits first.
    merge(base_ref)
    merge(upstream_ref)
    git("push", "origin", f"HEAD:refs/heads/{BRANCH}")
    if pulls:
        return f"Updated {pulls[0]['url']} through upstream {upstream_sha}."

    body = (
        f"Merge `thecem/hassio-evopt:main` through `{upstream_sha}` into `{base}`.\n\n"
        f"The pristine upstream state is stored on `{MIRROR}`. The merge retains "
        "fork history and customizations, including the optimizer source pin, GHCR "
        "builds and HiGHS setting. Conflicting keepalive timestamps use the fork's "
        "copy; the replaced Docker Hub updater stays removed. Other conflicts "
        "stop the workflow for manual resolution.\n\n"
        "Use **Create a merge commit** to retain upstream ancestry. Do not squash "
        "or rebase this sync PR. Run **Sync add-on upstream** again to refresh an "
        "open PR or create the next one after merging.\n"
    )
    with tempfile.TemporaryDirectory() as directory:
        body_file = Path(directory) / "body.md"
        body_file.write_text(body, encoding="utf-8")
        try:
            return gh("pr", "create", "--repo", repository, "--base", base,
                      "--head", BRANCH, "--title", "Sync add-on parent upstream",
                      "--body-file", str(body_file))
        except RuntimeError as error:
            raise RuntimeError(
                f"The sync branch was pushed, but PR creation failed: {error}\n"
                "If Actions is not allowed to create PRs, enable Settings > Actions > "
                "General > Allow GitHub Actions to create and approve pull requests.\n"
                f"You can also open https://github.com/{repository}/compare/{base}...{BRANCH}?expand=1"
            ) from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--base", default="main")
    args = parser.parse_args()
    try:
        message = sync(args.repository, args.base)
    except RuntimeError as error:
        message = str(error)
        code = 1
    else:
        code = 0
    print(message)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as output:
            output.write(message + "\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
