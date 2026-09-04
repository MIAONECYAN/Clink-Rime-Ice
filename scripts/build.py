#!/usr/bin/env python3
"""Build Clink zh.cime, zh.clex and zh.emoji.json from pinned Rime Ice data."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import struct
import unicodedata
from collections import defaultdict
from dataclasses import dataclass


PINYIN_RE = re.compile(r"[a-z]+(?: [a-z]+)*\Z")
DICTIONARIES = ("8105.dict.yaml", "base.dict.yaml", "ext.dict.yaml", "others.dict.yaml")
MAX_CANDIDATES = 16


@dataclass(frozen=True)
class Entry:
    text: str
    spaced_reading: str
    reading: str
    weight: float
    source_order: int

    @property
    def rank(self):
        return (-self.weight, self.source_order, len(self.text), self.text.encode("utf-8"))


def weight(raw: str | None) -> float:
    if not raw:
        return 100.0
    try:
        return float(raw.rstrip("%"))
    except ValueError:
        return 100.0


def dictionary_entries(path: pathlib.Path, source_order: int):
    body = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not body:
            body = raw.strip() == "..."
            continue
        if not raw or raw.lstrip().startswith("#"):
            continue
        fields = raw.split("\t")
        if len(fields) < 2:
            continue
        text = unicodedata.normalize("NFC", fields[0].strip())
        spaced = " ".join(fields[1].strip().lower().split())
        amount = weight(fields[2] if len(fields) > 2 else None)
        if text and PINYIN_RE.fullmatch(spaced) and amount > 0:
            yield Entry(text, spaced, spaced.replace(" ", ""), amount, source_order)


def load_entries(rime: pathlib.Path):
    entries = {}
    source_counts = {}
    for order, name in enumerate(DICTIONARIES):
        count = 0
        for entry in dictionary_entries(rime / "cn_dicts" / name, order):
            count += 1
            key = (entry.reading, entry.text)
            previous = entries.get(key)
            if previous is None or entry.rank < previous.rank:
                entries[key] = entry
        source_counts[name] = count
    return list(entries.values()), source_counts


def choose(entries: list[Entry]):
    ranked = sorted(entries, key=lambda item: item.rank)
    anchors = {}
    for entry in ranked:
        anchors.setdefault(entry.spaced_reading, entry)
    selected = {
        (entry.text, entry.spaced_reading): entry
        for entry in sorted(anchors.values(), key=lambda item: item.rank)[:MAX_CANDIDATES]
    }
    for entry in ranked:
        if len(selected) == MAX_CANDIDATES:
            break
        selected.setdefault((entry.text, entry.spaced_reading), entry)
    return sorted(selected.values(), key=lambda item: item.rank)


def write_cime(entries: list[Entry], path: pathlib.Path):
    groups = defaultdict(list)
    for entry in entries:
        groups[entry.reading].append(entry)
    slots = 0
    collisions = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for reading in sorted(groups):
            candidates = choose(groups[reading])
            slots += len(candidates)
            collisions += len({entry.spaced_reading for entry in groups[reading]}) > 1
            output.write("\t".join([reading, *(entry.text for entry in candidates)]) + "\n")
    return {"readings": len(groups), "candidate_slots": slots, "boundary_collisions": collisions}


def write_clex(entries: list[Entry], path: pathlib.Path):
    counts = {}
    for entry in entries:
        counts[entry.text] = max(counts.get(entry.text, 0.0), entry.weight)
    total = sum(counts.values())
    words = sorted(((word, count / total) for word, count in counts.items()), key=lambda row: row[0].encode())
    letters = {}
    for word, probability in words:
        for character in word:
            letters[character] = letters.get(character, 0.0) + probability
    alphabet = [character for character, _ in sorted(letters.items(), key=lambda row: -row[1])[:48]]
    index = {character: position for position, character in enumerate(alphabet)}
    rows = [[0.0] * len(alphabet) for _ in range(len(alphabet) + 1)]
    for word, probability in words:
        characters = list(word)
        if characters and characters[0] in index:
            rows[0][index[characters[0]]] += probability
        for left, right in zip(characters, characters[1:]):
            if left in index and right in index:
                rows[index[left] + 1][index[right]] += probability
    data = bytearray(b"CLEX" + struct.pack("<III", 1, len(words), len(alphabet)))
    for character in alphabet:
        data += struct.pack("<I", ord(character))
    for row in rows:
        maximum = max(row, default=0.0)
        data += bytes(round(255 * value / maximum) if maximum else 0 for value in row)
    offset = 0
    for word, _ in words:
        data += struct.pack("<I", offset)
        offset += len(word.encode())
    data += struct.pack("<I", offset)
    for _, probability in words:
        data.append(max(0, min(255, round((math.log10(probability) + 9) * 28))))
    for word, _ in words:
        data.append(min(255, len(word)))
    for word, _ in words:
        data += word.encode()
    path.write_bytes(data)
    return {"unique_words": len(words)}


def neutral_emoji(value: str):
    return "".join(character for character in value if character not in "\ufe0e\ufe0f" and not 0x1F3FB <= ord(character) <= 0x1F3FF)


def write_emoji(rime: pathlib.Path, path: pathlib.Path):
    aliases = defaultdict(list)
    for raw in (rime / "others" / "emoji-map.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        glyph = neutral_emoji(fields[0])
        if glyph.isascii() and glyph.isalnum():
            continue
        for alias in fields[1:]:
            if alias not in aliases[glyph]:
                aliases[glyph].append(alias)
    metadata = {
        "version": 1,
        "aliases": dict(sorted(aliases.items())),
        "stopwords": ["的", "了", "和", "是", "我", "你", "他", "她", "它", "在", "有", "就", "不", "也", "都", "与", "及"],
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"emoji_glyphs": len(aliases), "emoji_aliases": sum(map(len, aliases.values()))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rime-ice", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1] / "Lexicons")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    entries, sources = load_entries(args.rime_ice)
    report = {
        "sources": sources,
        "deduplicated_annotated_entries": len(entries),
        **write_cime(entries, args.output / "zh.cime"),
        **write_clex(entries, args.output / "zh.clex"),
        **write_emoji(args.rime_ice, args.output / "zh.emoji.json"),
    }
    report["bytes"] = {path.name: path.stat().st_size for path in sorted(args.output.glob("zh.*")) if path.is_file()}
    (args.output.parent / "BUILD_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
