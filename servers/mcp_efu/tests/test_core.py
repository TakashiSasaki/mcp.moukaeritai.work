import unittest
import sys
import shutil
from pathlib import Path
import os

# Add the project root to the path to allow running the module with -m
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from servers.mcp_efu.mcp_efu.core import (
    EfuFileManager,
    EPOCH_DIFFERENCE_SECONDS,
    HUNDREDS_OF_NANOSECONDS,
    FILE_ATTRIBUTE_DIRECTORY,
    FILE_ATTRIBUTE_ARCHIVE,
    FILE_ATTRIBUTE_READONLY,
    FILE_ATTRIBUTE_HIDDEN,
)


class TestEfuFileManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = PROJECT_ROOT / "test_temp_dir_for_core"
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / "normal.txt").write_text("hello")

        self.hidden_file = self.test_dir / ".hidden.txt"
        self.hidden_file.write_text("secret")

        self.readonly_file = self.test_dir / "readonly.txt"
        self.readonly_file.write_text("readonly")
        os.chmod(self.readonly_file, 0o444)

        self.subdir = self.test_dir / "subdir"
        self.subdir.mkdir(exist_ok=True)

        self.efu = EfuFileManager()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_unix_to_filetime_epoch(self):
        expected = EPOCH_DIFFERENCE_SECONDS * HUNDREDS_OF_NANOSECONDS
        self.assertEqual(self.efu._unix_to_filetime(0), expected)

    def test_get_file_list_includes_root_and_attributes(self):
        results = self.efu.get_file_list(str(self.test_dir))
        by_name = {item["filename"]: item for item in results}

        root_entry = by_name.get(str(self.test_dir.resolve()))
        self.assertIsNotNone(root_entry, "Root directory entry missing.")
        self.assertTrue(root_entry["attributes"] & FILE_ATTRIBUTE_DIRECTORY)

        hidden_entry = by_name.get(str(self.hidden_file.resolve()))
        self.assertIsNotNone(hidden_entry, "Hidden file entry missing.")
        self.assertTrue(hidden_entry["attributes"] & FILE_ATTRIBUTE_HIDDEN)
        self.assertTrue(hidden_entry["attributes"] & FILE_ATTRIBUTE_ARCHIVE)

        readonly_entry = by_name.get(str(self.readonly_file.resolve()))
        self.assertIsNotNone(readonly_entry, "Readonly file entry missing.")
        self.assertTrue(readonly_entry["attributes"] & FILE_ATTRIBUTE_READONLY)

        subdir_entry = by_name.get(str(self.subdir.resolve()))
        self.assertIsNotNone(subdir_entry, "Subdirectory entry missing.")
        self.assertTrue(subdir_entry["attributes"] & FILE_ATTRIBUTE_DIRECTORY)

    def test_invalid_path_raises(self):
        with self.assertRaises(ValueError):
            self.efu.get_file_list("/path/to/nonexistent/dir")

    def test_hashes_for_file(self):
        target = self.test_dir / "normal.txt"
        abs_target = str(target.absolute())
        real_target = str(target.resolve())
        self.assertEqual(
            self.efu.get_md5_hash(str(target)),
            {"path": abs_target, "realpath": real_target, "hash": "5d41402abc4b2a76b9719d911017c592"},
        )
        self.assertEqual(
            self.efu.get_sha1_hash(str(target)),
            {"path": abs_target, "realpath": real_target, "hash": "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"},
        )
        self.assertEqual(
            self.efu.get_git_blob_hash(str(target)),
            {"path": abs_target, "realpath": real_target, "hash": "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"},
        )

    def test_hash_invalid_path_raises(self):
        with self.assertRaises(ValueError):
            self.efu.get_md5_hash("/path/to/nonexistent/file.txt")


if __name__ == "__main__":
    unittest.main()
