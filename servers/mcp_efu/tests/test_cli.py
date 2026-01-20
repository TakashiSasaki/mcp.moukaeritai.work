import unittest
import subprocess
import sys
import os
import json
import shutil
from pathlib import Path

# Add the project root to the path to allow running the module with -m
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestCliMode(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory and files before each test."""
        self.test_dir = PROJECT_ROOT / "test_temp_dir_for_cli"
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / "file1.txt").write_text("hello")
        self.subdir = self.test_dir / "subdir"
        self.subdir.mkdir(exist_ok=True)
        (self.subdir / "file2.log").write_text("world")
        
        self.base_command = [sys.executable, "-m", "servers.mcp_efu.mcp_efu.main"]

    def tearDown(self):
        """Remove the temporary directory and its contents after each test."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_no_args_shows_help(self):
        """Test that running with no arguments shows help and exits with an error."""
        result = subprocess.run(self.base_command, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0, "Should exit with a non-zero status code.")
        self.assertIn("usage: main.py", result.stderr)
        self.assertIn("No command or server transport specified", result.stderr)

    def test_valid_path_to_stdout(self):
        """Test that a valid path prints a JSON list to stdout."""
        command = self.base_command + [str(self.test_dir)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Running in CLI mode", result.stderr)
        
        try:
            data = json.loads(result.stdout)
            self.assertIsInstance(data, list)
            # test_dir, file1.txt, subdir, subdir/file2.log (4 entries)
            self.assertEqual(len(data), 4)
            filenames = {item['filename'] for item in data}
            self.assertIn(str(self.test_dir.resolve()), filenames)
            self.assertIn(str((self.test_dir / "file1.txt").resolve()), filenames)
        except json.JSONDecodeError:
            self.fail("stdout is not valid JSON.")

    def test_nonexistent_path_error(self):
        """Test that a non-existent path results in an error."""
        command = self.base_command + ["/path/to/nonexistent/dir"]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is not a valid directory", result.stderr)
        
    def test_path_is_file_error(self):
        """Test that providing a file instead of a directory results in an error."""
        test_file = self.test_dir / "file1.txt"
        command = self.base_command + [str(test_file)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is not a valid directory", result.stderr)
        
    def test_mixed_args_error(self):
        """Test that mixing server and CLI arguments results in an error."""
        command = self.base_command + [str(self.test_dir), "--transport", "stdio"]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be used with --transport", result.stderr)
        
    def test_output_to_file(self):
        """Test that the --output option writes the result to a file."""
        output_file = self.test_dir / "output.json"
        command = self.base_command + [str(self.test_dir), "--output", str(output_file)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)

        self.assertEqual(result.returncode, 0)
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 4)

if __name__ == "__main__":
    unittest.main()
