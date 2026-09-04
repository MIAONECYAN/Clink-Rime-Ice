#!/usr/bin/env python3
"""Build a Clink community-repository release manifest and staged assets."""

import hashlib
import json
import pathlib
import shutil
import sys


if len(sys.argv) not in (4, 5):
    raise SystemExit("usage: build_manifest.py VERSION OWNER/REPO OUTPUT [CODE]")

version, repository, output_arg = sys.argv[1:4]
code = sys.argv[4] if len(sys.argv) == 5 else "zh_cn"
root = pathlib.Path(__file__).resolve().parents[1]
lexicons = root / "Lexicons"
output = pathlib.Path(output_arg)
assets = output / "assets"
entries = []

for path in sorted(lexicons.glob(code + ".*")):
    files = sorted(path.rglob("*")) if path.is_dir() else [path]
    for source in files:
        if not source.is_file() or source.name.startswith("._") or source.name == ".DS_Store":
            continue
        relative = source.relative_to(lexicons).as_posix()
        name = code + "--" + relative.replace("/", "--")
        target = assets / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        data = target.read_bytes()
        entries.append({
            "path": relative,
            "url": f"https://github.com/{repository}/releases/download/{version}/{name}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "byteCount": len(data),
        })

manifest = {"version": version, "packs": [{"code": code, "version": version, "assets": entries}]}
output.mkdir(parents=True, exist_ok=True)
(output / "manifest.json").write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
print(f"staged {len(entries)} assets for {repository} {version}")
