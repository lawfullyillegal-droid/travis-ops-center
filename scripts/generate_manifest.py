#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic SHA256SUMS for files."
    )

    parser.add_argument(
        "path",
        nargs="?",
        default="manifests",
        help="File or directory to hash.",
    )

    parser.add_argument(
        "--output",
        default="manifests/SHA256SUMS.txt",
    )

    args = parser.parse_args()

    target = Path(args.path)

    if not target.is_absolute():
        target = REPO_ROOT / target

    output = Path(args.output)

    if not output.is_absolute():
        output = REPO_ROOT / output

    if target.is_file():
        files = [target]

    elif target.is_dir():
        files = sorted(
            p for p in target.rglob("*")
            if p.is_file() and p.resolve() != output.resolve()
        )

    else:
        raise SystemExit(f"ERROR: path not found: {target}")

    lines = []

    for path in files:
        digest = sha256_file(path)

        try:
            display_path = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            display_path = str(path.resolve())

        lines.append(f"{digest}  {display_path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8",
    )

    print(f"Wrote {len(lines)} SHA-256 entries to {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
