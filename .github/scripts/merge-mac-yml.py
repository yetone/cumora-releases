#!/usr/bin/env python3
"""
Merge per-arch electron-builder `latest-mac.yml` feeds into a single yml
that lists every macOS artifact ONCE, with sha512 + size recomputed from
the actual files on disk.

The bash awk concat we used through v0.1.6 produced duplicate entries with
stale shas (each per-arch yml referenced both archs, but only one was
actually built / signed on that runner). Autoupdater picked the first
entry → sha mismatch on download → infinite retry loop.

This script is the source of truth:
  1. Walks `release/` for *.dmg + *.zip
  2. Computes sha512 (base64) + byte size for each
  3. Sorts arm64-first so the canonical top-level `path:` / `sha512:`
     points at the arm64 zip — that's the primary autoupdate channel
  4. Writes one entry per unique filename

Invoked from the release workflow's publish job:
    python3 .github/scripts/merge-mac-yml.py <version>
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import os
import sys

RELEASE = "release"


def real_sha_size(name: str) -> tuple[str, int]:
    """sha512 (base64) + byte size for an on-disk file under release/."""
    h = hashlib.sha512()
    n = 0
    with open(os.path.join(RELEASE, name), "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            n += len(chunk)
    return base64.b64encode(h.digest()).decode(), n


def is_mac(name: str) -> bool:
    return name.endswith(".dmg") or name.endswith(".zip")


def sort_key(name: str) -> tuple[int, int, str]:
    # arm64 first (so primary path resolves to arm64), then zips before
    # dmgs (autoupdater prefers zip), then alphabetic for stability.
    return (
        0 if "arm64" in name else 1,
        0 if name.endswith(".zip") else 1,
        name,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <version>", file=sys.stderr)
        return 2
    version = sys.argv[1]

    entries = sorted([f for f in os.listdir(RELEASE) if is_mac(f)], key=sort_key)
    if not entries:
        print("No mac artifacts in release/, skipping merged yml", file=sys.stderr)
        return 0

    release_date = datetime.datetime.utcnow().isoformat() + "Z"
    primary = entries[0]
    primary_sha, _ = real_sha_size(primary)

    out_path = os.path.join(RELEASE, "latest-mac.yml")
    with open(out_path, "w") as out:
        out.write(f"version: {version}\n")
        out.write("files:\n")
        for name in entries:
            sha, size = real_sha_size(name)
            out.write(f"  - url: {name}\n")
            out.write(f"    sha512: {sha}\n")
            out.write(f"    size: {size}\n")
        out.write(f"path: {primary}\n")
        out.write(f"sha512: {primary_sha}\n")
        out.write(f"releaseDate: '{release_date}'\n")

    print(f"Wrote {out_path} with {len(entries)} entries; primary={primary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
