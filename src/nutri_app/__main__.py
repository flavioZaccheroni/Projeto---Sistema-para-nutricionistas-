from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nutri_app.app.bootstrap import run


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
