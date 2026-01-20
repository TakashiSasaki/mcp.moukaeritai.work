# mcp_efu

`mcp_efu` is a server and command-line tool that generates file lists in a format compatible with the Everything File List (EFU). It can run as a persistent server communicating over TCP or stdio, or as a one-off command.

## Installation

This project is managed with [Poetry](https://python-poetry.org/).

1.  **Install Poetry**: Follow the instructions on the [official website](https://python-poetry.org/docs/#installation).

2.  **Navigate to the project directory**:
    ```bash
    cd /path/to/servers/mcp_efu
    ```

3.  **Install dependencies**:
    ```bash
    poetry install
    ```
    This command will create a virtual environment and install all the necessary dependencies defined in `pyproject.toml`.

## Usage (Running the Server)

After installation, the `mcp_efu` command is available within Poetry's virtual environment. You can run it using `poetry run` or by activating the virtual environment with `poetry shell`.

There are three modes of operation.

### 1. CLI Mode (One-off file listing)

This mode scans a directory and prints the file list to the console as a JSON object.

```bash
# Scan a directory and print to console
poetry run mcp_efu /path/to/your/directory

# Scan the current directory and save the output to a file
poetry run mcp_efu . --output file-list.json
```

### 2. STDIO Server Mode

This mode runs `mcp_efu` as a persistent server that communicates over `stdin` and `stdout` using JSON-RPC 2.0.

```bash
poetry run mcp_efu --transport stdio
```

### 3. TCP Server Mode

This mode runs `mcp_efu` as a persistent network server that listens for JSON-RPC 2.0 requests on a TCP socket.

```bash
# Run on localhost, port 8989
poetry run mcp_efu --transport tcp --host 127.0.0.1 --port 8989

# Run on all network interfaces
poetry run mcp_efu --transport tcp --host 0.0.0.0 --port 8989
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

This project uses Python's built-in `unittest` framework. Tests are located in the `tests/` directory.

To run the automated tests, first ensure you are in the project's root directory (`servers/mcp_efu`), then use the following command:

```bash
# Ensure you are in /path/to/servers/mcp_efu
poetry run python -m unittest discover
```

This command uses Poetry to execute the test runner within the project's managed virtual environment. It will automatically discover and run all tests.