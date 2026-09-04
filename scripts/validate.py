#!/usr/bin/env python3
"""Validate this repository's Clink language assets."""

import json
import pathlib
import re
import struct


ROOT = pathlib.Path(__file__).resolve().parents[1]
LEXICONS = ROOT / "Lexicons"
errors = []

clex = LEXICONS / "zh.clex"
if not clex.is_file():
    errors.append("missing Lexicons/zh.clex")
else:
    data = clex.read_bytes()
    if len(data) < 16 or data[:4] != b"CLEX" or struct.unpack_from("<I", data, 4)[0] != 1:
        errors.append("zh.clex is not CLEX version 1")

cime = LEXICONS / "zh.cime"
previous = ""
readings = 0
candidates = 0
if not cime.is_file():
    errors.append("missing Lexicons/zh.cime")
else:
    for number, raw in enumerate(cime.read_text(encoding="utf-8").splitlines(), 1):
        fields = raw.split("\t")
        reading, choices = fields[0], fields[1:]
        if not re.fullmatch(r"[a-z]+", reading):
            errors.append(f"zh.cime:{number}: invalid reading")
        if reading <= previous:
            errors.append(f"zh.cime:{number}: readings are not strictly sorted")
        if not choices or len(choices) > 16 or len(choices) != len(set(choices)) or any(not choice for choice in choices):
            errors.append(f"zh.cime:{number}: invalid candidates")
        previous = reading
        readings += 1
        candidates += len(choices)

emoji = LEXICONS / "zh.emoji.json"
try:
    metadata = json.loads(emoji.read_text(encoding="utf-8"))
    if metadata.get("version") != 1 or not isinstance(metadata.get("aliases"), dict) or not isinstance(metadata.get("stopwords"), list):
        errors.append("invalid zh.emoji.json schema")
except (OSError, json.JSONDecodeError) as error:
    errors.append(f"invalid zh.emoji.json: {error}")

for name in ("zh.cngm", "zh.bpevocab"):
    if not (LEXICONS / name).is_file():
        errors.append(f"missing Lexicons/{name}")
for name in ("metadata.json", "model.mil", "coremldata.bin", "weights/weight.bin", "analytics/coremldata.bin"):
    if not (LEXICONS / "zh.mlmodelc" / name).is_file():
        errors.append(f"missing Lexicons/zh.mlmodelc/{name}")

if errors:
    raise SystemExit("\n".join("ERROR: " + error for error in errors[:100]))
print(f"valid: {readings:,} readings, {candidates:,} candidate slots")
