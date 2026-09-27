"""Decrypt the pinned Mind2Web test.zip into a local per-step cache. Stdlib + /usr/bin/unzip.

The password ``mind2web`` is the one published in the official README (commit
33bd95ca); fetch_m2w.py checks that sentence before this runs. Members are streamed
with ``unzip -p`` (Info-ZIP, traditional PKWARE encryption) and never written out as
whole files. ``raw_html`` is dropped; each step keeps only what selection and rendering
need. The cache stays local: the authors ask that unzipped test files are not
redistributed online.

Output: ``<cache>/raw/steps.<split>.jsonl`` (source order: member, task, step) and
``<cache>/raw/extract-receipt.json`` with member CRC checks and output digests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

PASSWORD = "mind2web"  # published in the official README; not a credential
TEST_ZIP_SHA256 = "8f5fbe72afab942fe97cdf7fb397e179885d89b5c16862288e9a14bc6d41ca89"
SPLITS = ("test_task", "test_website", "test_domain")
STEP_FIELDS = ("action_uid", "operation", "pos_candidates", "neg_candidates", "cleaned_html")
TASK_FIELDS = ("annotation_id", "website", "domain", "subdomain", "confirmed_task", "action_reprs")


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache", type=Path, default=Path(os.environ.get("EXT_CACHE", ".")) / "m2w"
    )
    args = parser.parse_args(argv)
    archive = args.cache / "files/test.zip"
    digest = hashlib.sha256()
    with archive.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    if digest.hexdigest() != TEST_ZIP_SHA256:
        raise SystemExit("test.zip digest differs from the pin; refetch")
    members = sorted(zipfile.ZipFile(archive).infolist(), key=lambda info: info.filename)
    raw = args.cache / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, object] = {"test_zip_sha256": TEST_ZIP_SHA256, "members": [], "outputs": {}}
    handles = {split: (raw / f"steps.{split}.jsonl").open("w", encoding="utf-8") for split in SPLITS}
    try:
        for info in members:
            split = info.filename.split("/", 1)[0]
            if split not in SPLITS:
                raise SystemExit(f"unexpected member {info.filename}")
            data = subprocess.run(
                ["/usr/bin/unzip", "-p", "-P", PASSWORD, str(archive), info.filename],
                check=True,
                capture_output=True,
            ).stdout
            if len(data) != info.file_size or (zlib.crc32(data) & 0xFFFFFFFF) != info.CRC:
                raise SystemExit(f"{info.filename}: size/CRC mismatch after decryption")
            tasks = json.loads(data)
            del data
            steps = 0
            for task_index, task in enumerate(tasks):
                base = {key: task[key] for key in TASK_FIELDS}
                for step_index, action in enumerate(task["actions"]):
                    row = {
                        "split": split,
                        "member": info.filename,
                        "task_index": task_index,
                        "step_index": step_index,
                        "n_steps": len(task["actions"]),
                        **base,
                        **{key: action[key] for key in STEP_FIELDS},
                    }
                    handles[split].write(canonical(row) + "\n")
                    steps += 1
            receipt["members"].append(  # type: ignore[union-attr]
                {
                    "member": info.filename,
                    "file_size": info.file_size,
                    "crc32": f"{info.CRC:08x}",
                    "tasks": len(tasks),
                    "steps": steps,
                }
            )
            del tasks
    finally:
        for handle in handles.values():
            handle.close()
    for split in SPLITS:
        path = raw / f"steps.{split}.jsonl"
        output = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1 << 20):
                output.update(chunk)
        receipt["outputs"][path.name] = {  # type: ignore[index]
            "bytes": path.stat().st_size,
            "sha256": output.hexdigest(),
        }
    (raw / "extract-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    print(json.dumps(receipt["outputs"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
