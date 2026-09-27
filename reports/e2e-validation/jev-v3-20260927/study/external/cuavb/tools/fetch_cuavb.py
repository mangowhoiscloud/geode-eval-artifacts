"""Fetch the pinned CUAVerifierBench revision: text columns only, no screenshots.

Network: only huggingface.co (dataset API, card and files of microsoft/CUAVerifierBench)
and the CDN it redirects file downloads to. No token is read or sent.

Outputs under ``<cache>`` (default: $EXT_CACHE/cuavb):
  meta/api-revision.json, meta/tree.json   API answers for the pinned revision
  README.card.md                           dataset card at the pinned revision
  files/annotations/*.parquet              full files (small), sha256 == LFS oid checked
  raw/trajectories.text.jsonl              judge-input text columns, one row per trajectory
  raw/trajectories.labels.jsonl            verifier and human aggregate columns (never input)
  raw/annotations.jsonl                    one row per (task, reviewer) (never input)
  fetch-receipt.json                       byte ranges fetched per trajectories file + hashes

Trajectory parquet files hold inline PNG screenshots. They are read with HTTP range
requests limited to the footer and the listed text/label column chunks; the
``screenshots`` column is never requested. Requires pyarrow (GEODE uv env: 24.0.0).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = "microsoft/CUAVerifierBench"
REVISION = "c19eb323cd802add5c3d2840ff13044061364867"
API = f"https://huggingface.co/api/datasets/{REPO}"
RESOLVE = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}"
SPLITS = ("fara7b_om2w_browserbase", "internal")
INPUT_COLUMNS = (
    "task_id",
    "instruction",
    "init_url",
    "start_timestamp",
    "end_timestamp",
    "final_answer",
    "is_aborted",
    "web_surfer_log",
    "n_screenshots",
)
LABEL_COLUMNS = (
    "task_id",
    "gpt_eval_json",
    "uv_rubric_score",
    "uv_outcome_success",
    "mm_is_success",
    "verifier_is_success",
    "final_human_outcome_label",
    "final_human_process_label",
    "median_human_rubric_score_agnostic",
    "majority_human_outcome_vote",
)
FORBIDDEN_COLUMN = "screenshots"
USER_AGENT = "geode-jev-external-validation/1 (dataset fetch; no token)"


def _get(url: str, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RangeFile(io.RawIOBase):
    """Seekable read-only view of a remote file; every read is one HTTP range request."""

    def __init__(self, url: str, size: int) -> None:
        self.url, self.size, self.pos = url, size, 0
        self.fetched: list[dict[str, object]] = []

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.size, self.pos + n) - 1
        data = _get(self.url, {"Range": f"bytes={self.pos}-{end}"})
        if len(data) != end - self.pos + 1:
            raise OSError(f"short range read {len(data)} != {end - self.pos + 1}")
        self.fetched.append({"start": self.pos, "end": end, "sha256": _sha256(data)})
        self.pos += len(data)
        return data

    def readinto(self, buffer: bytearray) -> int:  # type: ignore[override]
        data = self.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)


def _rows(table: object) -> list[dict[str, object]]:
    return table.to_pylist()  # type: ignore[attr-defined]


def main(argv: list[str] | None = None) -> int:
    import pyarrow.parquet as pq

    parser = argparse.ArgumentParser(description=__doc__)
    default_cache = Path(os.environ.get("EXT_CACHE", ".")) / "cuavb"
    parser.add_argument("--cache", type=Path, default=default_cache)
    args = parser.parse_args(argv)
    cache: Path = args.cache
    for sub in ("meta", "files/annotations", "raw"):
        (cache / sub).mkdir(parents=True, exist_ok=True)

    revision_info = json.loads(_get(f"{API}/revision/{REVISION}"))
    if revision_info.get("sha") != REVISION or revision_info.get("gated") not in (False, None):
        raise SystemExit("pinned revision missing or dataset gated; stop and report")
    (cache / "meta/api-revision.json").write_text(
        json.dumps(revision_info, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    )
    tree = json.loads(_get(f"{API}/tree/{REVISION}?recursive=true"))
    (cache / "meta/tree.json").write_text(json.dumps(tree, indent=1, sort_keys=True) + "\n")
    files = {entry["path"]: entry for entry in tree if entry["type"] == "file"}

    card = _get(f"{RESOLVE}/README.md")
    (cache / "README.card.md").write_bytes(card)
    receipt: dict[str, object] = {
        "repo": REPO,
        "revision": REVISION,
        "card_sha256": _sha256(card),
        "annotations": {},
        "trajectories": {},
    }

    annotations: list[dict[str, object]] = []
    for split in SPLITS:
        path = f"annotations/{split}-00000-of-00001.parquet"
        data = _get(f"{RESOLVE}/{path}")
        expected = files[path]["lfs"]["oid"]
        if _sha256(data) != expected or len(data) != files[path]["size"]:
            raise SystemExit(f"{path}: sha256/size mismatch against the pinned tree")
        (cache / "files" / path).write_bytes(data)
        receipt["annotations"][path] = {"size": len(data), "sha256": expected}  # type: ignore[index]
        for row in _rows(pq.read_table(io.BytesIO(data))):
            annotations.append({"split": split, **row})

    text_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    for path in sorted(p for p in files if p.startswith("trajectories/")):
        split = path.split("/")[1].rsplit("-", 3)[0]
        if split not in SPLITS:
            raise SystemExit(f"unexpected trajectories file {path}")
        remote = RangeFile(f"{RESOLVE}/{path}", files[path]["size"])
        parquet = pq.ParquetFile(remote, pre_buffer=False)
        names = parquet.schema_arrow.names
        if FORBIDDEN_COLUMN not in names or not set(INPUT_COLUMNS + LABEL_COLUMNS) <= set(names):
            raise SystemExit(f"{path}: unexpected schema {names}")
        texts = _rows(parquet.read(columns=list(INPUT_COLUMNS)))
        labels = _rows(parquet.read(columns=list(LABEL_COLUMNS)))
        text_rows.extend({"split": split, **row} for row in texts)
        label_rows.extend({"split": split, **row} for row in labels)
        receipt["trajectories"][path] = {  # type: ignore[index]
            "size": files[path]["size"],
            "lfs_sha256_not_verified_locally": files[path]["lfs"]["oid"],
            "rows": parquet.metadata.num_rows,
            "row_groups": parquet.metadata.num_row_groups,
            "bytes_fetched": sum(int(r["end"]) - int(r["start"]) + 1 for r in remote.fetched),
            "ranges": remote.fetched,
        }

    def dump(name: str, rows: list[dict[str, object]], key: tuple[str, ...]) -> str:
        ordered = sorted(rows, key=lambda row: tuple(str(row.get(k)) for k in key))
        text = "".join(_canonical(row) + "\n" for row in ordered)
        (cache / "raw" / name).write_text(text, encoding="utf-8")
        return _sha256(text.encode())

    receipt["raw_sha256"] = {
        "trajectories.text.jsonl": dump("trajectories.text.jsonl", text_rows, ("split", "task_id")),
        "trajectories.labels.jsonl": dump(
            "trajectories.labels.jsonl", label_rows, ("split", "task_id")
        ),
        "annotations.jsonl": dump("annotations.jsonl", annotations, ("split", "task_id", "annotator")),
    }
    receipt["counts"] = {
        "trajectories": len(text_rows),
        "annotation_rows": len(annotations),
        "bytes_fetched_trajectories": sum(
            v["bytes_fetched"] for v in receipt["trajectories"].values()  # type: ignore[union-attr]
        ),
    }
    (cache / "fetch-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    )
    print(json.dumps({k: receipt[k] for k in ("revision", "raw_sha256", "counts")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
