# mcp_efu

`mcp_efu` is a server and command-line tool that generates file lists in a format compatible with the Everything File List (EFU). It can run as a persistent server communicating over TCP or stdio, or as a one-off command.

## Usage

This tool can be run directly using the Python module runner (`python -m`) without installation.

There are two main modes of operation: CLI Mode and Server Mode.

### CLI Mode

This mode is for running a single scan and printing the results.

**To scan a directory and print results to the console:**
```bash
# Scan the current directory
python -m servers.mcp_efu.mcp_efu.main .

# Scan a specific directory
python -m servers.mcp_efu.mcp_efu.main /path/to/scan
```

**To save the results to a file:**
Use the `-o` or `--output` option.
```bash
python -m servers.mcp_efu.mcp_efu.main . --output my_file_list.json
```

### Server Mode

This mode runs a persistent server that accepts requests via a specified transport. All log messages are printed to `stderr` to keep `stdout` clean for data.

**To start the server:**
Use the `--transport` flag.

```bash
# Start a server listening on stdio
python -m servers.mcp_efu.mcp_efu.main --transport stdio

# Start a server listening on a TCP port
python -m servers.mcp_efu.mcp_efu.main --transport tcp --host localhost --port 8989
```

## Protocol (Server Mode)

The server uses the **JSON-RPC 2.0** protocol over its transport. Each request and response should be a single, newline-terminated JSON object.

### Request Object

- `jsonrpc`: Must be `"2.0"`.
- `method`: The name of the method. Currently, only `"get_file_list"` is supported.
- `params`: A list of parameters.
  - For `get_file_list`, this should be a list containing a single string: the absolute path of the directory to scan.
- `id`: A unique identifier for the request.

**Example Request:**
```json
{"jsonrpc": "2.0", "method": "get_file_list", "params": ["/home/user/documents"], "id": 1}
```

### Response Object (Success)

- `jsonrpc`: `"2.0"`.
- `id`: The ID from the request.
- `result`: The data returned by the method. For `get_file_list`, this is a list of file/directory objects.

**Example Success Response:**
```json
{"id":1,"result":[{"filename":"/path/to/file.txt", "size":123, "date_modified": 134133637457112202, "date_created": 134133637457112202, "attributes": 32}],"jsonrpc":"2.0"}
```

### Response Object (Error)

- `jsonrpc`: `"2.0"`.
- `id`: The ID from the request.
- `error`: An object containing `code` and `message`.

**Example Error Response:**
```json
{"id":1,"error":{"code":-32000,"message":"Server error: Path '/nonexistent' is not a valid directory."},"jsonrpc":"2.0"}
```

## Testing

To run the automated tests for the CLI mode, use the `unittest` module. This command will automatically discover and run all tests within the `servers/mcp_efu/tests` directory.

```bash
python -m unittest discover servers/mcp_efu/tests
```

## Installation (Optional)

While not required for use, you can install the package if you wish to make the `mcp_efu` command globally available from your shell.

1.  **Navigate to the project directory**:
    ```bash
    cd servers/mcp_efu
    ```

2.  **Install the package in editable mode**:
    ```bash
    # It's good practice to use a virtual environment
    # python -m venv venv
    # source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    pip install -e .
    ```