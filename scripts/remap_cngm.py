#!/usr/bin/env python3
"""Bind an existing CNGM model to a new CLEX dictionary by word identity."""

import argparse
import hashlib
import json
from pathlib import Path
import struct


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_clex(path):
    data = Path(path).read_bytes()
    if len(data) < 16:
        raise ValueError("truncated CLEX header")
    magic, version, count, alphabet = struct.unpack_from("<4sIII", data)
    if magic != b"CLEX" or version != 1 or not count or alphabet > 48:
        raise ValueError("invalid CLEX v1 header")
    start = 16 + 4 * alphabet + (alphabet + 1) * alphabet
    pool = start + 4 * (count + 1) + 2 * count
    if pool > len(data):
        raise ValueError("truncated CLEX tables")
    offsets = struct.unpack_from(f"<{count + 1}I", data, start)
    if offsets[0] != 0 or pool + offsets[-1] != len(data):
        raise ValueError("invalid CLEX word pool size")
    if any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise ValueError("invalid CLEX word offsets")
    encoded = [data[pool + offsets[i]:pool + offsets[i + 1]] for i in range(count)]
    if any(a >= b for a, b in zip(encoded, encoded[1:])):
        raise ValueError("CLEX words must be unique and bytewise sorted")
    return [word.decode("utf-8") for word in encoded]


def read_cngm(path, word_count):
    data = Path(path).read_bytes()
    if len(data) < 12:
        raise ValueError("truncated CNGM header")
    magic, version, count = struct.unpack_from("<4sII", data)
    if magic != b"CNGM" or version != 1 or len(data) != 12 + 9 * count:
        raise ValueError("invalid CNGM v1 size or header")
    previous = struct.unpack_from(f"<{count}I", data, 12)
    following = struct.unpack_from(f"<{count}I", data, 12 + 4 * count)
    rows = list(zip(previous, following, data[12 + 8 * count:]))
    if any(a >= word_count or b >= word_count for a, b, _ in rows):
        raise ValueError("CNGM word ID outside its dictionary")
    if len({(a, b) for a, b, _ in rows}) != count:
        raise ValueError("duplicate CNGM pair")
    ranks = [(a, -score) for a, _, score in rows]
    if ranks != sorted(ranks):
        raise ValueError("CNGM groups or scores are not sorted")
    return rows


def remap(source_words, target_words, source_rows):
    target_ids = {word: index for index, word in enumerate(target_words)}
    rows = []
    for previous, following, score in source_rows:
        a = target_ids.get(source_words[previous])
        b = target_ids.get(source_words[following])
        if a is not None and b is not None:
            rows.append((a, b, score))
    # IDs change when the bytewise dictionary order changes. Rebuild the groups.
    return sorted(rows, key=lambda row: (row[0], -row[2], row[1]))


def encode_cngm(rows):
    data = bytearray(b"CNGM" + struct.pack("<II", 1, len(rows)))
    for column in (0, 1):
        for row in rows:
            data.extend(struct.pack("<I", row[column]))
    data.extend(row[2] for row in rows)
    return data


def verify_binding(lexicons, code, report_path, source_lexicons=None, source_code="zh"):
    clex = lexicons / f"{code}.clex"
    cngm = lexicons / f"{code}.cngm"
    words = read_clex(clex)
    rows = read_cngm(cngm, len(words))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("version") != 1 or report.get("code") != code:
        raise ValueError("invalid prediction binding report")
    expected = {"clex_sha256": digest(clex), "cngm_sha256": digest(cngm), "word_count": len(words)}
    if report.get("target") != expected or report.get("retained_pairs") != len(rows):
        raise ValueError("prediction report does not match the CLEX/CNGM pair; rebuild predictions")
    if source_lexicons is not None:
        source_clex = source_lexicons / f"{source_code}.clex"
        source_cngm = source_lexicons / f"{source_code}.cngm"
        old_words = read_clex(source_clex)
        old_rows = read_cngm(source_cngm, len(old_words))
        source = {"clex_sha256": digest(source_clex), "cngm_sha256": digest(source_cngm), "word_count": len(old_words)}
        if report.get("source") != source:
            raise ValueError("prediction source hashes do not match")
        # Compare decoded word pairs, not just legal numeric ID ranges or hashes.
        vocabulary = set(words)
        expected_pairs = {(old_words[a], old_words[b]): score for a, b, score in old_rows
                          if old_words[a] in vocabulary and old_words[b] in vocabulary}
        actual_pairs = {(words[a], words[b]): score for a, b, score in rows}
        if actual_pairs != expected_pairs:
            raise ValueError("prediction word identities or weights changed")
        if report.get("source_pairs") != len(old_rows) or report.get("dropped_pairs") != len(old_rows) - len(rows):
            raise ValueError("incorrect prediction coverage report")
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lexicons", type=Path, required=True)
    parser.add_argument("--source-code", default="zh")
    parser.add_argument("--lexicons", type=Path, default=Path(__file__).resolve().parents[1] / "Lexicons")
    parser.add_argument("--code", default="zh_cn")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    source_clex = args.source_lexicons / f"{args.source_code}.clex"
    source_cngm = args.source_lexicons / f"{args.source_code}.cngm"
    target_clex = args.lexicons / f"{args.code}.clex"
    target_cngm = args.lexicons / f"{args.code}.cngm"
    report_path = args.report or args.lexicons.parent / "PREDICTION_REPORT.json"
    source_words = read_clex(source_clex)
    target_words = read_clex(target_clex)
    source_rows = read_cngm(source_cngm, len(source_words))
    rows = remap(source_words, target_words, source_rows)
    if not rows:
        raise ValueError("no prediction pairs matched the target dictionary")
    target_cngm.write_bytes(encode_cngm(rows))
    report = {
        "version": 1, "code": args.code,
        "method": "word-identity remap; retain original quantized scores; drop missing words",
        "source": {"clex_sha256": digest(source_clex), "cngm_sha256": digest(source_cngm), "word_count": len(source_words)},
        "target": {"clex_sha256": digest(target_clex), "cngm_sha256": digest(target_cngm), "word_count": len(target_words)},
        "source_pairs": len(source_rows), "retained_pairs": len(rows),
        "dropped_pairs": len(source_rows) - len(rows),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    verify_binding(args.lexicons, args.code, report_path, args.source_lexicons, args.source_code)
    build_report_path = args.lexicons.parent / "BUILD_REPORT.json"
    if build_report_path.exists():
        build_report = json.loads(build_report_path.read_text(encoding="utf-8"))
        if build_report.get("code") == args.code:
            build_report["bytes"][target_cngm.name] = target_cngm.stat().st_size
            build_report_path.write_text(json.dumps(build_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
