"""Build the Jev v3 E2E payloads and Harbor task-bundle from option-E sources.

Contract: 05 v2 §2.3-§2.4, §8 and ``run-packets/e2e-payload/README.md`` §3-§5.
Run by the owner with sealed-source access; the Run owner receives hashes only.

Inputs
* the run folder's ``source-pin.json`` (fixed-SHA checkout);
* ``e2e-sources.json`` (``jev-v3.e2e-sources@1``, ``option`` "E"): second-author
  inbox files for ranks 1-12 (natural), 13-18 (injected) and 19-20 (spare), plus
  the admission rows, which are selection clusters given as ``FILE#cluster_id``
  (ranks 14 and 15 of the selection gold order);
* the Run packet slot matrix ``e2e-slots.jsonl``;
* optionally the public selection split manifest, to re-derive admission ranks.

Checks before any write: every file hash, the option-E salt (sha256 of the sorted,
concatenated source-file SHA-256 values), each rank as the position in
``sha256(source_id + salt)`` order, the admission ranks, and the slot matrix
against the ranks and the §2.4 cell rotation. Natural payloads carry no
intervention (task ``nat-<source_id>-<sha256(normalized payload)[:12]>``);
injected payloads come from ``noul_conditions.build_task`` (task
``noul-<source>-<digest12>``), shared by the Choice and Noul arms. Harbor task
directories are the hash-pinned r6 writer's output, staged and moved into place.

Outputs in the run folder, never overwritten: ``payloads/``, ``task-bundle/``,
``labels.jsonl`` (0600, withheld-sealed until its unit ends),
``e2e-sources.json`` (the input, copied) and ``payload-manifest.json`` (IDs,
cells and hashes; no gold). No model, network, Docker or credential access.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LEGACY_WRITER = Path("withheld-local-path-9f83c6114c42f833")
LEGACY_WRITER_SHA256 = "2efc952c9723392455a92b6562f2a45f5d67aa1019fae0958ce6440e9658869d"
E2E_UNITS = ("U0d", "U0e", "U0f", "U7r0", "U7r1", "U8c", "U8n")
ADMISSION_UNITS = frozenset({"U0d", "U0e", "U0f"})
SOURCES_SCHEMA = "jev-v3.e2e-sources@1"
MANIFEST_SCHEMA = "jev-v3.e2e-payload-manifest@1"
E_ROLES = ("natural", "injected", "spare")
INJECTED_CELLS = ("c1m0", "c0m1", "c1m1")
AUTHORITY = (
    "Synthetic inbox diagnostic tasks for the Jev v3 E2E units (option E, second-author "
    "sealed sources; admission from selection clusters). Not Terminal-Bench or a leaderboard. "
    "Payloads, tests/ and labels hold gold; the Run owner uses hashes only."
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode())


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def tree_sha256(directory: Path) -> str:
    """Digest of every regular file (relative path and bytes) under a task directory."""
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file() or p.is_symlink()):
        if path.is_symlink():
            raise ValueError(f"symlink in task tree: {path}")
        digest.update(str(path.relative_to(directory)).encode() + b"\0")
        digest.update(sha256_file(path).encode() + b"\n")
    return digest.hexdigest()


def load_legacy_writer(source: Path, *, path: Path = LEGACY_WRITER) -> Any:
    """The r6 Harbor task writer, hash-pinned, pointed at the pinned source."""
    if sha256_file(path) != LEGACY_WRITER_SHA256:
        raise ValueError("reused r6 task writer changed")
    spec = importlib.util.spec_from_file_location("jev_r6_task_writer", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load the r6 task writer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE = source
    return module


def _pending(value: object) -> bool:
    return isinstance(value, str) and "PENDING" in value


def split_file(spec: str, root: Path) -> tuple[Path, str | None]:
    """``FILE`` or ``FILE#selector``; relative files resolve under the sources root."""
    text, _, selector = spec.partition("#")
    path = Path(text)
    return (path if path.is_absolute() else root / path), (selector or None)


def load_source_list(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_id") != SOURCES_SCHEMA or document.get("option") != "E":
        raise ValueError("e2e-sources.json must be jev-v3.e2e-sources@1 with option E")
    rows = document.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("e2e-sources.json lists no sources")
    ids = [row.get("source_id") for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("source IDs repeat")
    return document


def _checked_file(row: Mapping[str, Any], root: Path) -> Path:
    if any(_pending(row.get(key)) for key in ("source_id", "file", "sha256")):
        raise ValueError(f"{row.get('source_id')}: source row is still PENDING")
    path, _ = split_file(row["file"], root)
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"{row['source_id']}: source file missing")
    if sha256_file(path) != row["sha256"]:
        raise ValueError(f"{row['source_id']}: source bytes differ from e2e-sources.json")
    return path


def option_e_order(
    document: Mapping[str, Any], root: Path, *, check_files: bool = True
) -> dict[str, list[dict[str, Any]]]:
    """Verify the option-E salt and every rank; return natural/injected rows in rank order.

    ``check_files=False`` is the public check: it uses only the listed digests and
    never opens a (sealed) source file.
    """
    rows = [dict(row) for row in document["sources"] if row.get("role") in E_ROLES]
    for row in rows:
        if not check_files:
            if any(_pending(row.get(key)) for key in ("source_id", "file", "sha256")):
                raise ValueError(f"{row.get('source_id')}: source row is still PENDING")
            continue
        _checked_file(row, root)
    salt = sha256_text("".join(sorted(row["sha256"] for row in rows)))
    if document.get("salt", {}).get("value") != salt:
        raise ValueError("option-E salt differs from the sorted source-file hashes")
    order = sorted(rows, key=lambda row: sha256_text(row["source_id"] + salt))
    for position, row in enumerate(order, start=1):
        expected = "natural" if position <= 12 else "injected" if position <= 18 else "spare"
        if row.get("rank") != position or row["role"] != expected:
            raise ValueError(f"{row['source_id']}: rank or role differs from the salted order")
        if expected == "injected" and sorted(row.get("cells") or ()) != sorted(INJECTED_CELLS):
            raise ValueError(f"{row['source_id']}: an injected source carries c1m0, c0m1 and c1m1")
    natural = [row for row in order if row["role"] == "natural"]
    injected = [row for row in order if row["role"] == "injected"]
    if len(natural) != 12 or len(injected) != 6 or len(order) > 20:
        raise ValueError("option E needs 12 natural, 6 injected and at most 2 spare sources")
    return {"natural": natural, "injected": injected}


def admission_rows(
    document: Mapping[str, Any], root: Path, selection_manifest: Path | None
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    """The selection-cluster admission sources; ranks re-derived when a manifest is given."""
    found = {
        row.get("role"): dict(row)
        for row in document["sources"]
        if row.get("role", "").startswith("admission-")
    }
    natural, injected = found.get("admission-natural"), found.get("admission-injected")
    if (
        natural is None
        or injected is None
        or len([r for r in document["sources"] if str(r.get("role")).startswith("admission-")]) != 2
    ):
        raise ValueError("exactly one admission-natural and one admission-injected source")
    if list(injected.get("cells") or ()) != ["c1m1"]:
        raise ValueError("the admission-injected source carries only c1m1")
    for row in (natural, injected):
        _checked_file(row, root)
        _, selector = split_file(row["file"], root)
        if selector != row["source_id"]:
            raise ValueError(f"{row['source_id']}: admission uses FILE#cluster_id")
    verified = False
    if selection_manifest is not None:
        selection = json.loads(selection_manifest.read_text(encoding="utf-8"))["splits"][
            "selection"
        ]
        gold = selection["gold_sha256"]
        files = {entry["cluster_id"]: entry["sha256"] for entry in selection["cluster_files"]}
        order = sorted(files, key=lambda cid: sha256_text(cid + gold))
        for row, position in ((natural, 14), (injected, 15)):
            if (
                order[position - 1] != row["source_id"]
                or row.get("rank") != position
                or gold not in str(row.get("rank_salt"))
                or files[row["source_id"]] != row["sha256"]
            ):
                raise ValueError(
                    f"{row['source_id']}: admission rank differs from the selection order"
                )
        verified = True
    return natural, injected, verified


def expected_workloads(
    natural: Sequence[str], injected: Sequence[str], admission: tuple[str, str]
) -> dict[str, list[tuple[str, str]]]:
    """Unit -> (task, cell) in slot order (packet generator and 05 v2 §2.4 rotation)."""
    u8 = [
        (task, cell)
        for j, task in enumerate(injected)
        for cell in INJECTED_CELLS[j % 3 :] + INJECTED_CELLS[: j % 3]
    ]
    adm_nat, adm_inj = admission
    return {
        "U0d": [(adm_nat, "natural"), (adm_inj, "c1m1")],
        "U0e": [(adm_inj, "c1m1")],
        "U0f": [(adm_nat, "natural"), (adm_inj, "c1m1")],
        "U7r0": [(task, "natural") for task in natural],
        "U7r1": [(task, "natural") for task in natural],
        "U8c": u8,
        "U8n": list(u8),
    }


def verify_public(
    *,
    sources_path: Path,
    sources_root: Path,
    slots_path: Path,
    selection_manifest: Path | None,
) -> dict[str, Any]:
    """Everything checkable without a sealed file (Run owner; before the fixed SHA).

    The salt and ranks come from the listed digests, the admission ranks from the
    public selection split, and the slot matrix must have no preview or placeholder
    rows, follow the §2.4 rotations (A/B pairs; C rotation for U7) and carry the
    ranked tasks. Only public selection cluster files are read.
    """
    from paired_dispatch import PREVIEW_SOURCES, load_slots

    document = load_source_list(sources_path)
    e_rows = option_e_order(document, sources_root, check_files=False)
    adm_nat, adm_inj, verified = admission_rows(document, sources_root, selection_manifest)
    rows = read_slot_rows(slots_path)
    natural = [row["source_id"] for row in e_rows["natural"]]
    injected = [row["source_id"] for row in e_rows["injected"]]
    check_slots(
        rows,
        expected_workloads(natural, injected, (adm_nat["source_id"], adm_inj["source_id"])),
        E2E_UNITS,
    )
    slots = {unit: load_slots(rows, unit, arm_c=unit == "U0f") for unit in E2E_UNITS}
    for unit in ("U7r0", "U7r1"):
        load_slots(rows, unit, arm_c=True)  # the frozen C rotation, too
    for unit, unit_slots in slots.items():
        if any(slot.source in PREVIEW_SOURCES for slot in unit_slots):
            raise ValueError(f"{unit}: preview or placeholder slot rows remain")
        if unit[:2] in {"U7", "U8"} and any(slot.arms != ("A", "B") for slot in unit_slots):
            raise ValueError(f"{unit}: every slot pairs arms A and B")
    if [s.task for s in slots["U7r1"]] != [s.task for s in slots["U7r0"]]:
        raise ValueError("U7r1 must repeat U7r0's tasks in the same order")
    if [s.workload_id for s in slots["U8n"]] != [s.workload_id for s in slots["U8c"]]:
        raise ValueError("U8n must use U8c's task-cells in the same order")
    return {
        "option": "E",
        "sources_sha256": sha256_file(sources_path),
        "slots_sha256": sha256_file(slots_path),
        "salt": document["salt"]["value"],
        "natural": natural,
        "injected": injected,
        "admission": [adm_nat["source_id"], f"{adm_inj['source_id']}#c1m1"],
        "admission_rank_verified": verified,
        "slots": {unit: len(unit_slots) for unit, unit_slots in slots.items()},
        "replay": [
            [slot.slot_id, slot.workload_id]
            for unit_slots in slots.values()
            for slot in unit_slots
            if slot.replay_preselected
        ],
        "sealed_files_opened": 0,
    }


def read_slot_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def check_slots(
    rows: Sequence[Mapping[str, Any]],
    expected: Mapping[str, list[tuple[str, str]]],
    units: Sequence[str],
) -> None:
    for unit in units:
        actual = [(row["task"], row["cell"]) for row in rows if row["unit"] == unit]
        if actual != expected[unit]:
            raise ValueError(f"{unit}: slot matrix tasks differ from the source ranks")


def workload_id(task: str, cell: str) -> str:
    return task if cell == "natural" else f"{task}#{cell}"


def natural_payload(source: Any) -> tuple[dict[str, Any], bytes]:
    from evals.benchmarks.decision_handoff_runtime import inbox_request, validate_inbox_case

    request = inbox_request(source.items)
    normalized = {
        "case": {"profile": "inbox", "request": request, "items": source.items},
        "orders": dict(source.orders),
        "intervention": None,
    }
    task_id = f"nat-{source.label}-{sha256_text(canonical(normalized))[:12]}"
    payload = {
        "case": {"id": task_id, "profile": "inbox", "request": request, "items": source.items},
        "orders": dict(source.orders),
        "intervention": None,
    }
    validate_inbox_case(payload["case"], payload["orders"])
    return payload, (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def _write_new(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def build(
    *,
    out: Path,
    sources_path: Path,
    sources_root: Path,
    slots_path: Path,
    source: Path,
    revision: str,
    units: Sequence[str] = E2E_UNITS,
    selection_manifest: Path | None = None,
    writer_path: Path = LEGACY_WRITER,
) -> dict[str, Any]:
    """Validate every source, rank and task first, then write; refuse existing outputs."""
    from evals.benchmarks import noul_conditions as noul
    from evals.platforms.harbor_handoff import _task

    out = out.resolve()
    unknown = set(units) - set(E2E_UNITS)
    if unknown or not units:
        raise ValueError(f"units must be a subset of {E2E_UNITS}")
    for name in (
        "task-bundle",
        "payloads",
        "labels.jsonl",
        "e2e-sources.json",
        "payload-manifest.json",
    ):
        if (out / name).exists():
            raise FileExistsError(f"{out / name} exists; E2E bundles are never overwritten")
    document = load_source_list(sources_path)
    adm_nat, adm_inj, admission_verified = admission_rows(
        document, sources_root, selection_manifest
    )
    e_rows: dict[str, list[dict[str, Any]]] = {"natural": [], "injected": []}
    if set(units) - ADMISSION_UNITS:
        e_rows = option_e_order(document, sources_root)
    rows_by_id = {row["source_id"]: row for group in e_rows.values() for row in group}
    rows_by_id.update({adm_nat["source_id"]: adm_nat, adm_inj["source_id"]: adm_inj})
    expected = expected_workloads(
        [row["source_id"] for row in e_rows["natural"]] or ["-"] * 12,
        [row["source_id"] for row in e_rows["injected"]] or ["-"] * 6,
        (adm_nat["source_id"], adm_inj["source_id"]),
    )
    check_slots(read_slot_rows(slots_path), expected, units)
    needed: dict[str, tuple[str, str]] = {}
    for unit in units:
        for task, cell in expected[unit]:
            needed.setdefault(workload_id(task, cell), (task, cell))
    sources: dict[str, Any] = {}
    for task in dict.fromkeys(task for task, _ in needed.values()):
        path, selector = split_file(rows_by_id[task]["file"], sources_root)
        loaded = noul.load_sources(str(path) + (f"#{selector}" if selector else ""))
        if len(loaded) != 1 or loaded[0].label != task:
            raise ValueError(f"{task}: a source file must hold exactly that source")
        sources[task] = loaded[0]
    plans = []
    for wid, (task, cell) in needed.items():
        if cell == "natural":
            payload, encoded = natural_payload(sources[task])
            label = None
        else:
            payload, label, encoded = noul.build_task(sources[task], cell)
        plans.append((wid, task, cell, payload, encoded, label))
    if len({plan[3]["case"]["id"] for plan in plans}) != len(plans):
        raise ValueError("two workloads share a task ID")
    writer = load_legacy_writer(source, path=writer_path)
    lock = writer.requirements()
    staging = out / f".staging-{uuid.uuid4().hex}"
    writer.ROOT = staging
    entries, labels = [], []
    try:
        for wid, task, cell, payload, encoded, label in plans:
            payload = json.loads(encoded)  # the task tree is a pure function of the payload bytes
            case = payload["case"]
            writer.make(case, payload["orders"], lock)
            (staging / "payloads" / f"{case['id']}.json").unlink()
            task_dir = out / "task-bundle" / case["id"]
            task_dir.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.rename(staging / "task-bundle" / case["id"], task_dir)
            case_file = out / "payloads" / f"{case['id']}.json"
            _write_new(case_file, encoded)
            checked = _task(case_file, sha256_file(case_file))
            if checked["case"] != json.loads((task_dir / "tests/case.json").read_text()):
                raise ValueError(f"{wid}: payload case differs from its task oracle case")
            if (task_dir / "instruction.md").read_text() != case["request"]:
                raise ValueError(f"{wid}: instruction differs from the frozen request")
            entries.append(
                {
                    "workload_id": wid,
                    "source_id": task,
                    "source_role": rows_by_id[task]["role"],
                    "cell": cell,
                    "case_id": case["id"],
                    "task_dir": f"task-bundle/{case['id']}",
                    "case_file": f"payloads/{case['id']}.json",
                    "case_sha256": sha256_file(case_file),
                    "task_tree_sha256": tree_sha256(task_dir),
                    "verifier_sha256": sha256_file(task_dir / "tests/verify.py"),
                    "verification_intervention": "verification_intervention" in payload,
                    "noul_truth": None
                    if cell == "natural"
                    else dict(
                        zip(
                            ("has_contradiction", "missing_evidence"), noul.CELLS[cell], strict=True
                        )
                    ),
                }
            )
            if label is not None:
                labels.append({"workload_id": wid, **label})
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    labels_raw = "".join(canonical(row) + "\n" for row in labels).encode()
    _write_new(out / "labels.jsonl", labels_raw)
    sources_raw = sources_path.read_bytes()
    _write_new(out / "e2e-sources.json", sources_raw)
    ordered = [entry["case_id"] for entry in entries]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "option": "E",
        "source_revision": revision,
        "image_digest": writer.IMAGE,
        "oracle_sha256": sha256_file(source / "evals/benchmarks/decision_handoff_runtime.py"),
        "noul_oracle_sha256": noul.oracle_sha256(),
        "uv_lock_sha256": sha256_file(source / "uv.lock"),
        "verifier_requirements_sha256": sha256_bytes(lock.encode()),
        "task_writer_sha256": LEGACY_WRITER_SHA256,
        "sources_sha256": sha256_bytes(sources_raw),
        "option_e_salt": document.get("salt", {}).get("value")
        if set(units) - ADMISSION_UNITS
        else None,
        "admission_rank_verified": admission_verified,
        "slots_sha256": sha256_file(slots_path),
        "units": list(units),
        "workloads": entries,
        "ordered_task_ids": ordered,
        "workload_ids_sha256": sha256_text(
            json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))
        ),
        "labels": "labels.jsonl",
        "labels_sha256": sha256_bytes(labels_raw),
        "labels_privacy": "withheld-sealed until the unit that uses them ends",
        "authority": AUTHORITY,
    }
    _write_new(
        out / "payload-manifest.json",
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(),
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    from source_pin import load_source_pin

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True, help="e2e-sources.json (option E)")
    parser.add_argument(
        "--sources-root", type=Path, required=True, help="base of relative source files"
    )
    parser.add_argument("--slots", type=Path, required=True)
    parser.add_argument("--selection-manifest", type=Path, help="public selection split manifest")
    parser.add_argument("--units", default=",".join(E2E_UNITS))
    parser.add_argument(
        "--verify-public", action="store_true", help="digest-only check; opens no sealed file"
    )
    args = parser.parse_args(argv)
    if args.verify_public:
        report = verify_public(
            sources_path=args.sources,
            sources_root=args.sources_root,
            slots_path=args.slots,
            selection_manifest=args.selection_manifest,
        )
        print(json.dumps(report, indent=2))
        return 0
    os.umask(0o077)
    source, revision = load_source_pin(ROOT)
    sys.path.insert(0, str(source))
    manifest = build(
        out=ROOT,
        sources_path=args.sources,
        sources_root=args.sources_root,
        slots_path=args.slots,
        source=source,
        revision=revision,
        units=[unit for unit in args.units.split(",") if unit],
        selection_manifest=args.selection_manifest,
    )
    print(
        json.dumps(
            {
                "workloads": len(manifest["workloads"]),
                "payload_manifest_sha256": sha256_file(ROOT / "payload-manifest.json"),
                "labels_sha256": manifest["labels_sha256"],
                "admission_rank_verified": manifest["admission_rank_verified"],
                "model_dispatches": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
