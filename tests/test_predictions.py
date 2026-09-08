import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build import Entry, write_clex
from remap_cngm import digest, encode_cngm, read_clex, read_cngm, remap, verify_binding


class PredictionsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def lexicon(self, name, words):
        path = self.root / name
        write_clex([Entry(w, "a", "a", 100, 0) for w in words], path)
        return path

    def test_reorder_drop_and_preserve_weights(self):
        rows = remap(["a", "b", "z"], ["0", "b", "z"],
                     [(0, 1, 220), (1, 2, 200), (1, 1, 90), (2, 1, 180)])
        self.assertEqual(rows, [(1, 2, 200), (1, 1, 90), (2, 1, 180)])
        # Inserted words shift every numeric ID, but not word-pair identities.
        self.assertEqual(remap(["a", "b"], ["0", "a", "b"], [(0, 1, 150)]), [(1, 2, 150)])

    def test_clex_round_trip_and_truncation(self):
        path = self.lexicon("words.clex", ["z", "a", "\u4f60", "\u597d"])
        self.assertEqual(read_clex(path), ["a", "z", "\u4f60", "\u597d"])
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaises(ValueError):
            read_clex(path)

    def test_invalid_cngm(self):
        path = self.root / "model.cngm"
        for rows in [[(0, 4, 100)], [(1, 0, 100), (0, 1, 100)],
                     [(0, 1, 100), (0, 1, 90)], [(0, 1, 90), (0, 2, 100)]]:
            with self.subTest(rows=rows):
                path.write_bytes(encode_cngm(rows))
                with self.assertRaises(ValueError):
                    read_cngm(path, 3)
        path.write_bytes(b"CNGM" + struct.pack("<II", 1, 1))
        with self.assertRaises(ValueError):
            read_cngm(path, 3)

    def test_semantic_verification_rejects_old_ids_even_with_updated_hashes(self):
        source = self.lexicon("zh.clex", ["a", "b"])
        target = self.lexicon("zh_cn.clex", ["0", "a", "b"])
        original = self.root / "zh.cngm"
        output = self.root / "zh_cn.cngm"
        original.write_bytes(encode_cngm([(0, 1, 150)]))
        output.write_bytes(encode_cngm([(1, 2, 150)]))
        report_path = self.root / "report.json"
        report = {
            "version": 1, "code": "zh_cn", "source_pairs": 1, "retained_pairs": 1, "dropped_pairs": 0,
            "source": {"clex_sha256": digest(source), "cngm_sha256": digest(original), "word_count": 2},
            "target": {"clex_sha256": digest(target), "cngm_sha256": digest(output), "word_count": 3},
        }
        report_path.write_text(json.dumps(report))
        self.assertEqual(verify_binding(self.root, "zh_cn", report_path, self.root), 1)
        output.write_bytes(original.read_bytes())
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_binding(self.root, "zh_cn", report_path)
        report["target"]["cngm_sha256"] = digest(output)
        report_path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "identities or weights"):
            verify_binding(self.root, "zh_cn", report_path, self.root)


if __name__ == "__main__":
    unittest.main()
