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
        # We run the package `mcp_efu` which should be available in the env.
        self.command = [
            sys.executable,
            "-m", "mcp_efu",
            "--transport", "stdio"
        ]
        self.server_process = None
        self.env = os.environ.copy()
        package_root = PROJECT_ROOT / "servers" / "mcp_efu"
        self.env["PYTHONPATH"] = str(package_root) + os.pathsep + self.env.get("PYTHONPATH", "")

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
            encoding='utf-8',
            env=self.env
        )

        # Read and discard the server/hello notification
        self.server_process.stdout.readline()

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
            encoding='utf-8',
            env=self.env
        )
        
        # Read and discard the server/hello notification
        self.server_process.stdout.readline()

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

    def test_stdio_tools_list(self):
        """Test a successful tools/list request over stdio."""
        self.server_process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=self.env
        )

        # Read and discard the server/hello notification
        self.server_process.stdout.readline()

        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "tools-list-1"
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
        self.assertEqual(response.get("id"), "tools-list-1")
        self.assertIn("result", response)
        
        result = response["result"]
        self.assertIn("tools", result)
        tools = result["tools"]
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 1)

        tool = tools[0]
        self.assertEqual(tool["name"], "get_file_list")
        self.assertIn("指定されたパス内のファイルとディレクトリの一覧を取得します。", tool["description"])
        
        input_schema = tool["inputSchema"]
        self.assertEqual(input_schema["type"], "object")
        self.assertIn("path", input_schema["properties"])
        self.assertEqual(input_schema["properties"]["path"]["type"], "string")
        self.assertEqual(input_schema["required"], ["path"])

    def test_stdio_server_hello_notification(self):
        """Test that the server sends a server/hello notification on connect."""
        self.server_process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=self.env
        )

        # The server should immediately send a `server/hello` notification.
        # We should be able to read it without sending any request.
        response_line = self.server_process.stdout.readline()
        self.assertTrue(response_line, "Server did not send the server/hello notification.")
        
        response = json.loads(response_line)

        # Assertions for server/hello notification
        self.assertEqual(response.get("jsonrpc"), "2.0")
        self.assertEqual(response.get("method"), "server/hello")
        self.assertNotIn("id", response)  # Notifications must not have an id

        params = response.get("params", {})
        self.assertEqual(params.get("displayName"), "EFU File Lister")
        self.assertIn("tools", params)
        
        tools = params["tools"]
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "get_file_list")

if __name__ == "__main__":
    unittest.main()
