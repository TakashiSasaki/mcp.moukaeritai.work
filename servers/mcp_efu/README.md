# mcp_efu

`mcp_efu` is a simple server that provides read-only access to a local filesystem. It can communicate over a TCP socket or via standard input/output (stdio), making it suitable for use by AI agents or other local processes.

The entire project is structured as an installable Python package.

## Installation

It is recommended to install the package in a virtual environment.

1.  **Navigate to the project directory**:
    ```bash
    cd servers/mcp_efu
    ```

2.  **Install the package in editable mode**:
    This allows you to modify the source code without reinstalling. The `.` refers to the current directory where `pyproject.toml` is located.
    ```bash
    # It's good practice to use a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`

    # Install the package
    pip install -e .
    ```
    After installation, the `mcp_efu` command will be available in your shell.


## Usage

The `mcp_efu` server can be started in two modes: `tcp` (default) or `stdio`. All log messages are printed to `stderr` to keep `stdout` clean for data responses in stdio mode.

### TCP Mode

This is the default mode. The server will listen on a specified host and port.

**To start the server:**
```bash
# Start server with default settings (localhost:8989, serving current directory)
mcp_efu

# Start server on a different port and with a specific root directory
mcp_efu --port 9000 --root /home/user/documents
```

**To test the connection (using `netcat` or `nc`):**
1.  Open a new terminal.
2.  Connect to the server: `nc localhost 8989`
3.  Send a JSON request followed by a newline:
    ```json
    {"method": "list_directory", "params": {"path": "."}}
    ```
4.  The server will respond with a list of files and directories in JSON format and wait for the next request.

### Stdio Mode

In this mode, the server reads requests from `stdin` and writes responses to `stdout`.

**To start the server:**
```bash
mcp_efu --mode stdio
```

**To test:**
1.  The server will wait for input.
2.  Paste or type a JSON request and press Enter:
    ```json
    {"method": "list_directory", "params": {"path": "."}}
    ```
3.  The server will print the JSON response to `stdout` and wait for the next request.

## Protocol

The server uses a simple line-delimited JSON protocol. Each request and response is a single line of text terminated by a newline character (`\\n`).

### Request Format

A JSON object with two keys:
- `method`: The name of the method to call. Currently, only `"list_directory"` is supported.
- `params`: A dictionary of parameters for the method.
  - For `list_directory`, the only parameter is `"path"`, which is the relative path from the server's root directory.

**Example Request:**
```json
{"method": "list_directory", "params": {"path": "mcp_efu"}}
```

### Response Format

A JSON object with a `status` key and either a `data` or `message` key.

- `status`: Either `"success"` or `"error"`.
- `data` (on success): The result of the method. For `list_directory`, this is a list of objects, each containing `name`, `path`, and `is_dir`.
- `message` (on error): A string describing the error.

**Example Success Response:**
```json
{"status": "success", "data": [{"name": "__init__.py", "path": "mcp_efu/__init__.py", "is_dir": false}, {"name": "main.py", "path": "mcp_efu/main.py", "is_dir": false}]}
```

**Example Error Response:**
```json
{"status": "error", "message": "Access denied: Path is outside the root directory."}
```
