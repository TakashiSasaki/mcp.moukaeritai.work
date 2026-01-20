
import unittest
import subprocess
import sys
import os
import json
import shutil
from pathlib import Path
import time
import socket
from contextlib import closing


# Add the project root to the path to allow running the module with -m
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

class TestTcpServerMode(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory and files before each test."""
        self.test_dir = PROJECT_ROOT / "test_temp_dir_for_tcp"
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / "tcp_file1.txt").write_text("tcp-hello")
        self.subdir = self.test_dir / "tcp_subdir"
        self.subdir.mkdir(exist_ok=True)
        (self.subdir / "tcp_file2.log").write_text("tcp-world")
        
        self.port = find_free_port()
        self.host = "127.0.0.1"

        # Command to run the server in tcp mode.
        self.command = [
            sys.executable,
            "-m", "mcp_efu.main",
            "--transport", "tcp",
            "--port", str(self.port),
            "--host", self.host
        ]
        self.server_process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        # Wait for the server to start
        time.sleep(1) 

    def tearDown(self):
        """Remove temp directory and terminate server process."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        self.server_process.terminate()
        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_process.kill()
            self.server_process.wait(timeout=5)
        
        # Capture and print stderr for debugging if tests fail
        stderr_output = self.server_process.stderr.read()
        if stderr_output:
            print(f"TCP Server Stderr:\n{stderr_output}", file=sys.stderr)


    def test_tcp_get_file_list_success(self):
        """Test a successful get_file_list request over TCP."""
        try:
            with socket.create_connection((self.host, self.port), timeout=5) as sock:
                with sock.makefile('rw', encoding='utf-8') as f:
                    request = {
                        "jsonrpc": "2.0",
                        "method": "get_file_list",
                        "params": [str(self.test_dir)],
                        "id": 1
                    }
                    
                    # Send request
                    f.write(json.dumps(request) + '\n')
                    f.flush()

                    # Read response
                    response_line = f.readline()
                    self.assertTrue(response_line, "Server did not respond.")
                    
                    response = json.loads(response_line)

                    # Assertions
                    self.assertEqual(response.get("jsonrpc"), "2.0")
                    self.assertEqual(response.get("id"), 1)
                    self.assertIn("result", response)
                    
                    result = response["result"]
                    self.assertIsInstance(result, list)
                    self.assertEqual(len(result), 4) # test_dir, file1, subdir, file2
                    filenames = {item['filename'] for item in result}
                    self.assertIn(str(self.test_dir.resolve()), filenames)
                    self.assertIn(str((self.test_dir / "tcp_file1.txt").resolve()), filenames)
        except ConnectionRefusedError:
            self.fail("Could not connect to the TCP server. Is it running?")
        except Exception as e:
            self.fail(f"An exception occurred: {e}")


    def test_tcp_invalid_path_error(self):
        """Test an error response for a non-existent path over TCP."""
        try:
            with socket.create_connection((self.host, self.port), timeout=3) as sock:
                with sock.makefile('rw', encoding='utf-8') as f:
                    request = {
                        "jsonrpc": "2.0",
                        "method": "get_file_list",
                        "params": ["/path/to/nonexistent/dir"],
                        "id": 2
                    }

                    # Send request
                    f.write(json.dumps(request) + '\n')
                    f.flush()

                    # Read response
                    response_line = f.readline()
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
        except ConnectionRefusedError:
            self.fail("Could not connect to the TCP server. Is it running?")

if __name__ == "__main__":
    unittest.main()
