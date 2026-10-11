import tempfile
from pathlib import Path
import unittest

from wordcloud import build_report, count_file, font_size


class WordCloudTests(unittest.TestCase):
    def test_thresholds_and_tied_maximum(self):
        for count, expected in [(10, "Huge"), (7, "Big"), (6, "Normal"),
                                (4, "Normal"), (3, "Small"), (2, "Small")]:
            with self.subTest(count=count):
                self.assertEqual(font_size(count, 10), expected)

    def test_tokenization(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_text("Apple, APPLE! Don't don’t café CAFÉ 123 foo_bar", encoding="utf-8-sig")
            self.assertEqual(count_file(path),
                             {"apple": 2, "don't": 2, "café": 2, "foo": 1, "bar": 1})

    def test_merge_filter_sort_and_repeat_run(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for index in range(5):
                (folder / f"{index}.txt").write_text("Apple banana", encoding="utf-8")
            (folder / "extra.TXT").write_text("pear pear unique", encoding="utf-8")
            (folder / "ignored.csv").write_text("ignored ignored", encoding="utf-8")
            output = folder / "report.txt"
            expected = ("word\tcount\tfont_size\napple\t5\tHuge\n"
                        "banana\t5\tHuge\npear\t2\tNormal\n")
            for _ in range(2):
                self.assertEqual(build_report(folder, output), 6)
                self.assertEqual(output.read_text(encoding="utf-8"), expected)

    def test_empty_and_singleton_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            output = folder / "report.txt"
            for content in ["", "one two three"]:
                (folder / "input.txt").write_text(content, encoding="utf-8")
                build_report(folder, output)
                self.assertEqual(output.read_text(encoding="utf-8"), "word\tcount\tfont_size\n")

    def test_missing_folder_and_no_text_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for source in [folder, folder / "missing"]:
                with self.subTest(source=source), self.assertRaises(ValueError):
                    build_report(source, folder / "report.txt")


if __name__ == "__main__":
    unittest.main()
