"""Model-free self-test: the mock rehearsals in ``tests/`` against this folder's pinned checkout.

    <pinned checkout interpreter> -B self_test.py

Fake Astra (subscription route identity), MockTransport Jev, synthetic account claims
and a fake key; no model, Docker, credential or network. Exit 0 only if every
rehearsal and guard scenario passes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    import pytest
    import source_pin

    source, _ = source_pin.load_source_pin(HERE)
    os.environ["JEV3_PANEL_SOURCE"] = str(source)
    sys.path.insert(1, str(source))  # pinned synthetic helper fixtures, before pytest collection
    os.chdir(source)
    return int(
        pytest.main(
            [
                "-q",
                "-p",
                "no:cacheprovider",
                "-c",
                os.devnull,
                "--rootdir",
                str(HERE),
                str(HERE / "tests"),
            ]
        )
    )


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    raise SystemExit(main())
