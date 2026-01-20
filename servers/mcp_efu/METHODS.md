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
- `filename`: Absolute path to the entry.
- `size`: File size in bytes (directories are `0`).
- `date_modified`: Windows FILETIME 64-bit integer.
- `date_created`: Windows FILETIME 64-bit integer.
- `attributes`: Windows-style attribute flags.

### Notes
- The root directory itself is included as the first entry.
- Entries that cannot be accessed due to permissions are skipped.
- If `path` is not a directory, the tool returns an error.
- The returned `filename` values are absolute paths.
- Date fields are always converted to Windows FILETIME 64-bit integers, regardless of platform.

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

## get_md5_hash

Returns the MD5 hash of a file given its full path.

### When to use
- You need an MD5 digest for a specific file.

### Input
- `path` (string, required): Absolute or relative path to the file.

### Output
An object containing:
- `path`: Absolute path to the file.
- `realpath`: Canonical path with symlinks resolved.
- `hash`: Lowercase hexadecimal MD5 string.

### Notes
- If `path` is not a file, the tool returns an error.
- The returned `path` is always absolute.
- The returned `realpath` is the resolved canonical path.

### Example
Input:
```json
{"path": "/home/user/file.txt"}
```

Output (example):
```json
{"path": "/home/user/file.txt", "realpath": "/home/user/file.txt", "hash": "5eb63bbbe01eeed093cb22bb8f5acdc3"}
```

## get_sha1_hash

Returns the SHA1 hash of a file given its full path.

### When to use
- You need a SHA1 digest for a specific file.

### Input
- `path` (string, required): Absolute or relative path to the file.

### Output
An object containing:
- `path`: Absolute path to the file.
- `realpath`: Canonical path with symlinks resolved.
- `hash`: Lowercase hexadecimal SHA1 string.

### Notes
- If `path` is not a file, the tool returns an error.
- The returned `path` is always absolute.
- The returned `realpath` is the resolved canonical path.

### Example
Input:
```json
{"path": "/home/user/file.txt"}
```

Output (example):
```json
{"path": "/home/user/file.txt", "realpath": "/home/user/file.txt", "hash": "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"}
```

## get_git_blob_hash

Returns the Git blob SHA1 hash of a file given its full path.

### When to use
- You need the Git blob hash for a file without invoking Git.

### Input
- `path` (string, required): Absolute or relative path to the file.

### Output
An object containing:
- `path`: Absolute path to the file.
- `realpath`: Canonical path with symlinks resolved.
- `hash`: Lowercase hexadecimal Git blob SHA1 string.

### Notes
- The hash matches Git's `hash-object` output for the same file.
- If `path` is not a file, the tool returns an error.
- The returned `path` is always absolute.
- The returned `realpath` is the resolved canonical path.

### Example
Input:
```json
{"path": "/home/user/file.txt"}
```

Output (example):
```json
{"path": "/home/user/file.txt", "realpath": "/home/user/file.txt", "hash": "95d09f2b10159347eece71399a7e2e907ea3df4f"}
```
