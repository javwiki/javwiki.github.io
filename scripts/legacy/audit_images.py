#!/usr/bin/env python3
"""Compatibility entry point for the current image inventory.

The old filename-based classifier scanned the removed src/ tree and could
report zero reviewed pages. It also incorrectly treated filenames as proof.
Use scripts/checks/audit_images.py for the supported command.
"""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "checks" / "audit_images.py"),
        run_name="__main__",
    )
