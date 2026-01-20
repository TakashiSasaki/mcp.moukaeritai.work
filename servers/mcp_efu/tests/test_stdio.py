import hashlib
import json
import os
import shutil
import sys
import unittest
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

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
        self._timeout_seconds = 5

    def tearDown(self):
        """Remove temp directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _server_params(self) -> StdioServerParameters:
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_efu", "--transport", "stdio"],
            cwd=str(PROJECT_ROOT / "servers" / "mcp_efu"),
            env=os.environ.copy(),
        )

    @asynccontextmanager
    async def _session(self):
        params = self._server_params()
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(
                read_stream,
                write_stream,
                read_timeout_seconds=timedelta(seconds=self._timeout_seconds),
            ) as session:
                await session.initialize()
                yield session

    def _content_to_json(self, result):
        self.assertFalse(result.isError)
        self.assertTrue(result.content)
        blocks = [
            block.text for block in result.content if getattr(block, "type", None) == "text"
        ]
        self.assertTrue(blocks)
        parsed = [json.loads(block) for block in blocks]
        if len(parsed) == 1:
            return parsed[0]
        return parsed

    def _content_to_text(self, result):
        self.assertTrue(result.content)
        return "".join(
            block.text for block in result.content if getattr(block, "type", None) == "text"
        )

    def _run_async(self, coro):
        async def runner():
            with anyio.fail_after(self._timeout_seconds):
                return await coro()

        return anyio.run(runner)

    def test_stdio_initialize(self):
        async def run():
            async with stdio_client(self._server_params()) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    result = await session.initialize()
                    self.assertEqual(result.serverInfo.name, "EFU File Lister")

        self._run_async(run)

    def test_stdio_tools_list(self):
        async def run():
            async with self._session() as session:
                result = await session.list_tools()
                tool_names = {tool.name for tool in result.tools}
                self.assertEqual(
                    tool_names,
                    {"get_file_list", "get_md5_hash", "get_sha1_hash", "get_git_blob_hash"},
                )

        self._run_async(run)

    def test_stdio_get_file_list_success(self):
        async def run():
            async with self._session() as session:
                result = await session.call_tool(
                    "get_file_list", {"path": str(self.test_dir)}
                )
                payload = self._content_to_json(result)
                self.assertIsInstance(payload, list)
                self.assertEqual(len(payload), 4)
                filenames = {item["filename"] for item in payload}
                self.assertIn(str(self.test_dir.resolve()), filenames)
                self.assertIn(
                    str((self.test_dir / "server_file1.txt").resolve()),
                    filenames,
                )

        self._run_async(run)

    def test_stdio_invalid_path_error(self):
        async def run():
            async with self._session() as session:
                result = await session.call_tool(
                    "get_file_list", {"path": "/path/to/nonexistent/dir"}
                )
                self.assertTrue(result.isError)
                message = self._content_to_text(result)
                self.assertIn("not a valid directory", message)

        self._run_async(run)

    def test_stdio_hash_methods(self):
        async def run():
            async with self._session() as session:
                target = self.test_dir / "server_file1.txt"
                target_str = str(target)
                expected_path = str(target.absolute())
                expected_realpath = str(target.resolve())
                contents = target.read_bytes()
                requests = [
                    ("get_md5_hash", hashlib.md5(contents).hexdigest()),
                    ("get_sha1_hash", hashlib.sha1(contents).hexdigest()),
                    (
                        "get_git_blob_hash",
                        hashlib.sha1(f"blob {len(contents)}\0".encode() + contents).hexdigest(),
                    ),
                ]

                for method, digest in requests:
                    result = await session.call_tool(method, {"path": target_str})
                    payload = self._content_to_json(result)
                    self.assertEqual(
                        payload,
                        {
                            "path": expected_path,
                            "realpath": expected_realpath,
                            "hash": digest,
                        },
                    )

        self._run_async(run)


if __name__ == "__main__":
    unittest.main()
