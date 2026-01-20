# MCP Methods: mcp_efu

This document describes the MCP tools provided by the `mcp_efu` server in a human-readable form.

## get_file_list

Scans a directory and returns an EFU-compatible list of files and directories.

### When to use
- You need a complete inventory of files and folders under a given path.
- You want EFU-style metadata for each entry (size, timestamps, attributes).

### Input
- `path` (string, required): Absolute or relative path to the directory to scan.

### Output
An array of entries. Each entry is an object with:
- `filename`: Full path to the entry.
- `size`: File size in bytes (directories are `0`).
- `date_modified`: Windows FILETIME integer.
- `date_created`: Windows FILETIME integer.
- `attributes`: Windows-style attribute flags.

### Notes
- The root directory itself is included as the first entry.
- Entries that cannot be accessed due to permissions are skipped.
- If `path` is not a directory, the tool returns an error.

### Example
Input:
```json
{"path": "/home/user/documents"}
```

Output (shape example):
```json
[
  {
    "filename": "/home/user/documents",
    "size": 0,
    "date_modified": 134133637457112202,
    "date_created": 134133637457112202,
    "attributes": 16
  },
  {
    "filename": "/home/user/documents/file.txt",
    "size": 123,
    "date_modified": 134133637457112202,
    "date_created": 134133637457112202,
    "attributes": 32
  }
]
```
