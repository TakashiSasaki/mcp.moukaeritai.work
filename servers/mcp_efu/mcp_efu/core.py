# mcp_efu/core.py
import os
import json
from pathlib import Path

class FileSystemManager:
    """
    Handles read-only access to the filesystem within a specific root directory.
    """
    def __init__(self, root_path: str):
        """
        Initializes the FileSystemManager with a specific root directory.

        Args:
            root_path: The absolute or relative path to the directory that will
                       serve as the root for all file operations.
        
        Raises:
            ValueError: If the root_path is not a valid directory.
        """
        self.root_path = Path(root_path).resolve()
        if not self.root_path.is_dir():
            raise ValueError(f"Root path '{self.root_path}' is not a valid directory.")

    async def handle_request(self, request_str: str) -> str:
        """
        Parses a JSON request and calls the appropriate method.
        Currently, only 'list_directory' is supported.
        """
        try:
            request = json.loads(request_str)
            method = request.get("method")
            params = request.get("params", {})

            if method == "list_directory":
                path = params.get("path", ".")
                return await self.list_directory(path)
            else:
                return self._create_error_response(f"Unknown method: {method}")
        except json.JSONDecodeError:
            return self._create_error_response("Invalid JSON request.")
        except Exception as e:
            return self._create_error_response(f"An unexpected error occurred: {e}")

    async def list_directory(self, request_path: str) -> str:
        """
        Lists the contents of a directory in a JSON-RPC-like format.

        Args:
            request_path: The relative path from the root_path.

        Returns:
            A JSON string representing the list of files and directories,
            or an error message.
        """
        try:
            # Prevent directory traversal: resolve the path and check if it's within the root
            target_path = (self.root_path / request_path).resolve()
            if self.root_path not in target_path.parents and target_path != self.root_path:
                return self._create_error_response("Access denied: Path is outside the root directory.")

            if not target_path.exists():
                return self._create_error_response(f"Path does not exist: '{request_path}'")

            if not target_path.is_dir():
                 return self._create_error_response(f"Path is not a directory: '{request_path}'")

            contents = []
            for entry in os.scandir(target_path):
                contents.append({
                    "name": entry.name,
                    "path": str(Path(request_path) / entry.name),
                    "is_dir": entry.is_dir(),
                })
            
            return self._create_success_response(contents)

        except Exception as e:
            return self._create_error_response(f"Failed to list directory: {e}")

    def _create_success_response(self, data):
        return json.dumps({"status": "success", "data": data}) + "\\n"

    def _create_error_response(self, message):
        return json.dumps({"status": "error", "message": message}) + "\\n"
