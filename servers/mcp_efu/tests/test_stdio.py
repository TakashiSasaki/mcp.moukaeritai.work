import unittest
import subprocess
import sys
import os
import json
import shutil
from pathlib import Path
import time
import threading

# Add the project root to the path to allow running the module with -m
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestStdioServerMode(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory and files before each test."""
        self.test_dir = PROJECT_ROOT / "test_temp_dir_for_server"
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / "server_file1.txt").write_text("server-hello")
        self.subdir = self.test_dir / "server_subdir"
        self.subdir.mkdir(exist_ok=True)
        (self.subdir / "server_file2.log").write_text("server-world")
        
        # Command to run the server in stdio mode.
        # We run the module `mcp_efu.main` which should be available in the poetry env.
        self.command = [
            sys.executable,
            "-m", "servers.mcp_efu.mcp_efu.main",
            "--transport", "stdio"
        ]
        self.server_process = None

    def tearDown(self):
        """Remove temp directory and terminate server process."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        if self.server_process:
            # Gently try to close streams first
            if self.server_process.stdin:
                self.server_process.stdin.close()
            
            # Terminate the process
            self.server_process.terminate()
            try:
                # Wait for the process to terminate
                self.server_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self.server_process.kill()
                # Wait again to ensure it's gone
                self.server_process.wait(timeout=2)
            
            # Close the other streams after the process has ended
            if self.server_process.stdout:
                self.server_process.stdout.close()
            if self.server_process.stderr:
                self.server_process.stderr.close()

    def test_stdio_get_file_list_success(self):
        """Test a successful get_file_list request over stdio."""
        self.server_process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        # Give the server a moment to start
        time.sleep(0.5)

        request = {
            "jsonrpc": "2.0",
            "method": "get_file_list",
            "params": [str(self.test_dir)],
            "id": 1
        }
        
        # Send request
        self.server_process.stdin.write(json.dumps(request) + '\n')
        self.server_process.stdin.flush()

        # Read response
        response_line = self.server_process.stdout.readline()
        self.assertTrue(response_line, "Server did not respond.")
        
        response = json.loads(response_line)

        # Assertions
        self.assertEqual(response.get("jsonrpc"), "2.0")
        self.assertEqual(response.get("id"), 1)
        self.assertIn("result", response)
        
        result = response["result"]
        self.assertIsInstance(result, list)
        # test_dir, file1, subdir, file2 (4 entries)
        self.assertEqual(len(result), 4)
        filenames = {item['filename'] for item in result}
        self.assertIn(str(self.test_dir.resolve()), filenames)
        self.assertIn(str((self.test_dir / "server_file1.txt").resolve()), filenames)

    def test_stdio_invalid_path_error(self):
        """Test an error response for a non-existent path over stdio."""
        self.server_process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Give the server a moment to start
        time.sleep(0.5)

        request = {
            "jsonrpc": "2.0",
            "method": "get_file_list",
            "params": ["/path/to/nonexistent/dir"],
            "id": 2
        }

        # Send request
        self.server_process.stdin.write(json.dumps(request) + '\n')
        self.server_process.stdin.flush()

        # Read response
        response_line = self.server_process.stdout.readline()
        self.assertTrue(response_line, "Server did not respond.")

        response = json.loads(response_line)
        
        # Assertions
        self.assertEqual(response.get("jsonrpc"), "2.0")
        self.assertEqual(response.get("id"), 2)
        self.assertIn("error", response)
        self.assertNotIn("result", response)
        
        error = response["error"]
        self.assertEqual(error.get("code"), -32000)
        self.assertIn("is not a valid directory", error.get("message"))

if __name__ == "__main__":
    unittest.main()
