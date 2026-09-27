"""Fetch the pinned Mind2Web test archive and its access terms. Stdlib only.

Network: huggingface.co (osunlp/Mind2Web API, card, test.zip and its CDN redirect)
and the official GitHub repository OSU-NLP-Group/Mind2Web (API + README at a pinned
commit). No login, token or consent step exists on this path; the script stops if the
dataset reports gated access.

The test split is distributed only as a password-protected zip "to prevent potential
data contamination"; the password is published in the official README. The authors ask
not to redistribute the unzipped files online, so every file derived from it stays in
the local cache (publication class reproducible-cache).

Outputs under ``<cache>`` (default: $EXT_CACHE/m2w):
  meta/api-revision.json, meta/tree.json, meta/gh-commit.json
  README.card.md, github-README.md
  files/test.zip          (sha256 checked against the pinned LFS oid)
  fetch-receipt.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = "osunlp/Mind2Web"
REVISION = "17ece8eb89862368edc0cc806acee6fca5163474"
TEST_ZIP_SHA256 = "8f5fbe72afab942fe97cdf7fb397e179885d89b5c16862288e9a14bc6d41ca89"
TEST_ZIP_SIZE = 567_745_122
GITHUB_REPO = "OSU-NLP-Group/Mind2Web"
GITHUB_COMMIT = "33bd95caeee7bba22dd08ecc935845e15c5e5dc7"
API = f"https://huggingface.co/api/datasets/{REPO}"
RESOLVE = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}"
USER_AGENT = "geode-jev-external-validation/1 (dataset fetch; no token)"


def get(url: str, accept: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=600) as r:
        return r.read()


def download(url: str, target: Path) -> str:
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    partial = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(request, timeout=600) as response, partial.open("wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
    partial.replace(target)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache", type=Path, default=Path(os.environ.get("EXT_CACHE", ".")) / "m2w"
    )
    args = parser.parse_args(argv)
    cache: Path = args.cache
    for sub in ("meta", "files"):
        (cache / sub).mkdir(parents=True, exist_ok=True)

    info = json.loads(get(f"{API}/revision/{REVISION}"))
    if info.get("sha") != REVISION or info.get("gated") not in (False, None):
        raise SystemExit("pinned revision missing or gated; stop and report (no consent step)")
    (cache / "meta/api-revision.json").write_text(json.dumps(info, indent=1, sort_keys=True))
    tree = json.loads(get(f"{API}/tree/{REVISION}?recursive=true"))
    (cache / "meta/tree.json").write_text(json.dumps(tree, indent=1, sort_keys=True))
    entry = next(item for item in tree if item.get("path") == "test.zip")
    if entry["size"] != TEST_ZIP_SIZE or entry["lfs"]["oid"] != TEST_ZIP_SHA256:
        raise SystemExit("test.zip at the pinned revision differs from the preregistered pin")
    card = get(f"{RESOLVE}/README.md")
    (cache / "README.card.md").write_bytes(card)
    commit = json.loads(
        get(
            f"https://api.github.com/repos/{GITHUB_REPO}/commits/{GITHUB_COMMIT}",
            "application/vnd.github+json",
        )
    )
    (cache / "meta/gh-commit.json").write_text(
        json.dumps(
            {"sha": commit.get("sha"), "date": commit.get("commit", {}).get("committer", {})},
            indent=1,
            sort_keys=True,
        )
    )
    readme = get(f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_COMMIT}/README.md")
    (cache / "github-README.md").write_bytes(readme)
    text = readme.decode("utf-8")
    terms = {
        "password_published_in_readme": "unzip it with password `mind2web`" in text,
        "no_redistribution_notice": "Please DO NOT redistribute the unzipped data files online."
        in text,
        "dataset_license_cc_by_4": "Creative Commons Attribution 4.0 International License"
        in text,
    }
    if not all(terms.values()):
        raise SystemExit(f"official access terms changed: {terms}; stop and report")

    target = cache / "files/test.zip"
    if target.exists() and target.stat().st_size == TEST_ZIP_SIZE:
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
    else:
        actual = download(f"{RESOLVE}/test.zip", target)
    if actual != TEST_ZIP_SHA256:
        raise SystemExit(f"test.zip sha256 {actual} != pinned {TEST_ZIP_SHA256}")
    receipt = {
        "repo": REPO,
        "revision": REVISION,
        "card_sha256": hashlib.sha256(card).hexdigest(),
        "github_commit": GITHUB_COMMIT,
        "github_readme_sha256": hashlib.sha256(readme).hexdigest(),
        "terms": terms,
        "test_zip": {"size": TEST_ZIP_SIZE, "sha256": actual},
        "downloaded_bytes": TEST_ZIP_SIZE,
    }
    (cache / "fetch-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
