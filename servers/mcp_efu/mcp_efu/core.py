# mcp_efu/core.py
import hashlib
import os
import stat
from pathlib import Path

# Constants for FILETIME conversion
EPOCH_DIFFERENCE_SECONDS = 11644473600
HUNDREDS_OF_NANOSECONDS = 10_000_000

# Basic Windows file attributes
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_ARCHIVE = 0x20
FILE_ATTRIBUTE_READONLY = 0x01
FILE_ATTRIBUTE_HIDDEN = 0x02

class EfuFileManager:
    """
    Scans a directory and generates a file list in the EFU format.
    """

    def get_file_list(self, root_path_str: str) -> list[dict]:
        """
        Recursively walks through the given path and collects file information
        in the EFU format.
        """
        root_path = Path(root_path_str).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Path '{root_path_str}' is not a valid directory.")

        file_list = []
        # Add the root path itself to the list
        try:
            stat_info = root_path.stat(follow_symlinks=False)
            file_list.append({
                "filename": str(root_path),
                "size": 0,
                "date_modified": self._unix_to_filetime(stat_info.st_mtime),
                "date_created": self._unix_to_filetime(stat_info.st_ctime),
                "attributes": self._get_attributes(root_path, stat_info, True)
            })
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(f"Cannot access root path '{root_path_str}': {e}")


        for dirpath, dirnames, filenames in os.walk(root_path):
            entries = [(d, True) for d in dirnames] + [(f, False) for f in filenames]
            for name, is_dir in entries:
                full_path = Path(dirpath) / name
                try:
                    stat_info = full_path.stat(follow_symlinks=False)
                    
                    file_list.append({
                        "filename": str(full_path),
                        "size": stat_info.st_size if not is_dir else 0,
                        "date_modified": self._unix_to_filetime(stat_info.st_mtime),
                        "date_created": self._unix_to_filetime(stat_info.st_ctime),
                        "attributes": self._get_attributes(full_path, stat_info, is_dir)
                    })
                except (FileNotFoundError, PermissionError):
                    continue
        return file_list

    def get_md5_hash(self, file_path_str: str) -> dict:
        """Returns the MD5 hash for the given file path."""
        file_path, real_path = self._resolve_file_path(file_path_str)
        return {
            "path": str(file_path),
            "realpath": str(real_path),
            "hash": self._hash_file(file_path, hashlib.md5()),
        }

    def get_sha1_hash(self, file_path_str: str) -> dict:
        """Returns the SHA1 hash for the given file path."""
        file_path, real_path = self._resolve_file_path(file_path_str)
        return {
            "path": str(file_path),
            "realpath": str(real_path),
            "hash": self._hash_file(file_path, hashlib.sha1()),
        }

    def get_git_blob_hash(self, file_path_str: str) -> dict:
        """Returns the Git blob SHA1 hash for the given file path."""
        file_path, real_path = self._resolve_file_path(file_path_str)
        hasher = hashlib.sha1()
        size = file_path.stat().st_size
        header = f"blob {size}\0".encode()
        hasher.update(header)
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return {
            "path": str(file_path),
            "realpath": str(real_path),
            "hash": hasher.hexdigest(),
        }

    def _unix_to_filetime(self, unix_timestamp: float) -> int:
        """Converts a UNIX timestamp to a Windows FILETIME integer."""
        return int(unix_timestamp * HUNDREDS_OF_NANOSECONDS) + (EPOCH_DIFFERENCE_SECONDS * HUNDREDS_OF_NANOSECONDS)

    def _resolve_file_path(self, file_path_str: str) -> tuple[Path, Path]:
        input_path = Path(file_path_str).expanduser()
        file_path = input_path if input_path.is_absolute() else (Path.cwd() / input_path)
        real_path = file_path.resolve()
        if not file_path.is_file():
            raise ValueError(f"Path '{file_path_str}' is not a valid file.")
        return file_path, real_path

    def _hash_file(self, file_path: Path, hasher: "hashlib._Hash") -> str:
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _get_attributes(self, path: Path, stat_info, is_dir: bool) -> int:
        """Gets basic Windows-like attributes from stat info."""
        attrs = 0
        if not (stat_info.st_mode & stat.S_IWUSR):
            attrs |= FILE_ATTRIBUTE_READONLY
        
        if path.name.startswith('.'):
             attrs |= FILE_ATTRIBUTE_HIDDEN

        if is_dir:
            attrs |= FILE_ATTRIBUTE_DIRECTORY
        else:
            attrs |= FILE_ATTRIBUTE_ARCHIVE

        return attrs
