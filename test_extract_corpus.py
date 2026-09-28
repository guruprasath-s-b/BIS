import unittest

from extract_corpus import chunk_text


class ChunkTextTests(unittest.TestCase):
    def test_rejects_invalid_chunk_configuration(self):
        with self.assertRaises(ValueError):
            chunk_text("one two three", max_chunk_size=0)
        with self.assertRaises(ValueError):
            chunk_text("one two three", max_chunk_size=3, overlap=3)
        with self.assertRaises(ValueError):
            chunk_text("one two three", max_chunk_size=3, overlap=-1)

    def test_preserves_overlap_for_valid_configuration(self):
        text = "sterilization requirements surgical instruments validation procedures"
        chunks = chunk_text(text, max_chunk_size=3, overlap=1)
        self.assertEqual(chunks, [
            "sterilization requirements surgical",
            "surgical instruments validation",
        ])


if __name__ == "__main__":
    unittest.main()