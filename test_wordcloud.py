import tempfile
from pathlib import Path
import unittest
import subprocess
import sys
from unittest.mock import patch

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

    def test_canonical_unicode_and_nondecimal_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unicode.txt"
            path.write_text("café cafe\u0301 CAFÉ ² Ⅳ ١٢٣ naïve nai\u0308ve हिंदी हिंदी", encoding="utf-8")
            self.assertEqual(count_file(path), {"café": 3, "naïve": 2, "हिंदी": 2})

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(Path(__file__).with_name("wordcloud.py")),
                               *map(str, arguments)], capture_output=True, text=True)

    def test_cli_success_and_argument_error(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "input.txt").write_text("apple apple banana", encoding="utf-8")
            output = folder / "report.txt"
            result = self.run_cli(folder, "-o", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("apple\t2\tHuge", output.read_text(encoding="utf-8"))
            self.assertNotIn("banana", output.read_text(encoding="utf-8"))
        self.assertEqual(self.run_cli().returncode, 2)

    def test_cli_decoding_failure_names_file_and_preserves_report(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "good.txt").write_text("apple apple", encoding="utf-8")
            bad = folder / "bad.txt"
            bad.write_bytes(b"broken \xff")
            output = folder / "report.txt"
            output.write_text("previous report", encoding="utf-8")
            result = self.run_cli(folder, "-o", output)
            self.assertEqual(result.returncode, 1)
            self.assertIn(str(bad), result.stderr)
            self.assertIn("may be stale", result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")

    def test_cli_missing_folder_and_output_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "input.txt").write_text("apple apple", encoding="utf-8")
            self.assertEqual(self.run_cli(folder / "missing").returncode, 1)
            result = self.run_cli(folder, "-o", folder / "missing" / "report.txt")
            self.assertEqual(result.returncode, 1)
            self.assertIn("No new report", result.stderr)
            output = folder / "report-directory.txt"
            output.mkdir()
            self.assertEqual(self.run_cli(folder, "-o", output).returncode, 1)
            self.assertEqual(list(folder.glob('.wordcloud-*.tmp')), [])

    def test_failed_atomic_replace_preserves_destination_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "input.txt").write_text("apple apple", encoding="utf-8")
            output = folder / "report.txt"
            output.write_text("previous report", encoding="utf-8")
            with patch("wordcloud.os.replace", side_effect=OSError("simulated replacement failure")):
                with self.assertRaises(OSError):
                    build_report(folder, output)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")
            self.assertEqual(list(folder.glob('.wordcloud-*.tmp')), [])

    def test_large_multiline_input(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path = folder / "large.txt"
            with path.open("w", encoding="utf-8") as stream:
                for _ in range(50000):
                    stream.write("Alpha alpha café cafe\u0301 singleton\n")
            self.assertEqual(count_file(path), {"alpha": 100000, "café": 100000, "singleton": 50000})

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
