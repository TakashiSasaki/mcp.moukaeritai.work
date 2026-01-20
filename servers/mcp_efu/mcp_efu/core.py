# mcp_efu/core.py
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

    def _unix_to_filetime(self, unix_timestamp: float) -> int:
        """Converts a UNIX timestamp to a Windows FILETIME integer."""
        return int(unix_timestamp * HUNDREDS_OF_NANOSECONDS) + (EPOCH_DIFFERENCE_SECONDS * HUNDREDS_OF_NANOSECONDS)

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