#!/usr/bin/env python3
"""Merge base into PR branch, resolve simple conflicts, approve or escalate."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

BOT_LOGINS = {"github-actions", "github-actions[bot]", "cursor[bot]"}

# Lockfiles: keep the PR branch version when both sides changed the lockfile.
OURS_ONLY_PATTERNS = (
    r"(^|/)poetry\.lock$",
    r"(^|/)uv\.lock$",
    r"(^|/)Pipfile\.lock$",
    r"(^|/)package-lock\.json$",
    r"(^|/)yarn\.lock$",
    r"(^|/)pnpm-lock\.yaml$",
    r"(^|/)Cargo\.lock$",
    r"(^|/)Gemfile\.lock$",
)


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def gh_api(path: str) -> dict | list:
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def post_comment(body: str) -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    token = os.environ["GH_TOKEN"]
    payload = json.dumps({"body": body}).encode()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        response.read()


def approve_pr() -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    token = os.environ["GH_TOKEN"]
    payload = json.dumps({"event": "APPROVE", "body": "Auto-approved: PR is mergeable."}).encode()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode()
        # Already approved or cannot approve own PR — comment instead of failing the job.
        if error.code in {403, 422}:
            post_comment(
                "PR is mergeable, but this workflow could not submit an approval "
                f"(GitHub returned {error.code}). Details:\n\n```\n{detail}\n```"
            )
            return
        raise


def already_approved() -> bool:
    reviews = gh_api(f"/pulls/{os.environ['PR_NUMBER']}/reviews")
    for review in reviews:
        author = (review.get("user") or {}).get("login", "")
        if author in BOT_LOGINS and review.get("state") == "APPROVED":
            return True
    return False


def contributor_logins() -> list[str]:
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    pr = gh_api(f"/pulls/{pr_number}")
    commits = gh_api(f"/pulls/{pr_number}/commits")

    logins: set[str] = set()
    author = (pr.get("user") or {}).get("login")
    if author and author not in BOT_LOGINS:
        logins.add(author)

    for commit in commits:
        login = (commit.get("author") or {}).get("login")
        if login and login not in BOT_LOGINS:
            logins.add(login)

    try:
        review_requests = gh_api(f"/pulls/{pr_number}/requested_reviewers")
        for user in review_requests.get("users", []):
            login = user.get("login")
            if login and login not in BOT_LOGINS:
                logins.add(login)
    except urllib.error.HTTPError:
        pass

    return sorted(logins)


def mention_line(logins: list[str]) -> str:
    if not logins:
        return "_No human contributors found to mention._"
    return " ".join(f"@{login}" for login in logins)


def conflict_files() -> list[str]:
    result = run(["git", "diff", "--name-only", "--diff-filter=U"], check=False)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_ours_only_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(re.search(pattern, normalized) for pattern in OURS_ONLY_PATTERNS)


def resolve_ours_only_conflicts() -> list[str]:
    resolved: list[str] = []
    for path in conflict_files():
        if is_ours_only_file(path):
            run(["git", "checkout", "--ours", path])
            run(["git", "add", path])
            resolved.append(path)
    return resolved


def conflict_regions(path: str) -> list[str]:
    try:
        content = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return [f"- `{path}` (could not read file)"]

    regions: list[str] = []
    pattern = re.compile(
        r"^<<<<<<< .*?\n(.*?)^=======\n(.*?)^>>>>>>> .*?$",
        re.MULTILINE | re.DOTALL,
    )
    for index, match in enumerate(pattern.finditer(content), start=1):
        ours = match.group(1).strip()
        theirs = match.group(2).strip()
        ours_preview = ours[:240] + ("…" if len(ours) > 240 else "")
        theirs_preview = theirs[:240] + ("…" if len(theirs) > 240 else "")
        regions.append(
            f"- `{path}` (region {index})\n"
            f"  - **PR branch:** `{ours_preview or '(empty)'}`\n"
            f"  - **`main`:** `{theirs_preview or '(empty)'}`"
        )
    if not regions:
        regions.append(f"- `{path}` (conflict markers present)")
    return regions


def escalate(unresolved: list[str], resolved_lockfiles: list[str]) -> None:
    logins = contributor_logins()
    regions: list[str] = []
    for path in unresolved:
        regions.extend(conflict_regions(path))

    lockfile_note = ""
    if resolved_lockfiles:
        lockfile_note = (
            "\n\nAuto-resolved lockfiles (kept PR branch version):\n"
            + "\n".join(f"- `{path}`" for path in resolved_lockfiles)
        )

    body = (
        "## Merge conflicts need human input\n\n"
        f"{mention_line(logins)}\n\n"
        "This PR conflicts with `main`. Some conflicts need a human decision "
        "before this workflow can finish merging and approving.\n\n"
        "**Unresolved files:**\n"
        + "\n".join(f"- `{path}`" for path in unresolved)
        + "\n\n**Conflict details:**\n"
        + "\n".join(regions)
        + lockfile_note
        + "\n\nPlease resolve the conflicts (or reply here with guidance). "
        "This workflow will not approve until the PR is mergeable."
    )
    post_comment(body)
    print("Escalated unresolved conflicts to contributors.")
    sys.exit(0)


def main() -> None:
    base_ref = os.environ["BASE_REF"]
    pr_number = os.environ["PR_NUMBER"]

    run(["git", "fetch", "origin", base_ref])

    merge = run(["git", "merge", f"origin/{base_ref}", "--no-edit"], check=False)
    if merge.returncode == 0:
        merge_output = merge.stdout + merge.stderr
        if "Already up to date" in merge_output:
            if already_approved():
                print("Already up to date and approved.")
                return
            post_comment(
                f"PR is up to date with `{base_ref}` and mergeable — approving."
            )
        else:
            run(["git", "push", "origin", "HEAD"])
            post_comment(
                f"Merged latest `{base_ref}` into this branch. "
                "No conflicts found — approving."
            )

        if not already_approved():
            approve_pr()
        return

    if "CONFLICT" not in merge.stdout + merge.stderr:
        raise RuntimeError(f"Unexpected merge failure:\n{merge.stdout}\n{merge.stderr}")

    resolved_lockfiles = resolve_ours_only_conflicts()
    remaining = conflict_files()

    if remaining:
        escalate(remaining, resolved_lockfiles)
        return

    run(["git", "commit", "--no-edit"])
    run(["git", "push", "origin", "HEAD"])
    post_comment(
        "Merged latest `main`, auto-resolved straightforward lockfile conflicts, "
        "and pushed the update — approving."
    )
    if not already_approved():
        approve_pr()


if __name__ == "__main__":
    main()
