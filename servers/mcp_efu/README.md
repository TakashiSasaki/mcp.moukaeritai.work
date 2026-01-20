# mcp_efu

`mcp_efu` is a server and command-line tool that generates file lists in a format compatible with the Everything File List (EFU). It can run as a persistent server communicating over TCP or stdio, or as a one-off command.

## Modes of Operation

`mcp_efu` can be run in three distinct modes depending on your needs.

### 1. CLI Mode (Command-Line Interface)

This mode is designed for direct, interactive use by a person in a terminal. It functions as a simple, one-off command to scan a directory and see the results immediately.

*   **Function:** Scans a specified local directory path.
*   **Output:** Prints a JSON-formatted list of file information to standard output.
*   **Use Case:** Manually inspecting the contents of a directory or scripting simple file operations in a shell environment.
*   **Example:**
    ```bash
    # Scan a directory and print to console
    python -m servers.mcp_efu.mcp_efu.main /path/to/your/directory

    # Scan and save the output to a file
    python -m servers.mcp_efu.mcp_efu.main . --output file-list.json
    ```

### 2. STDIO Server Mode

This mode runs `mcp_efu` as a persistent server process that communicates over standard input (`stdin`) and standard output (`stdout`). It is designed for machine-to-machine communication, where one process controls another.

*   **Function:** Listens for JSON-RPC 2.0 requests on `stdin` and sends responses to `stdout`. All log messages are sent to `stderr` to keep the data channel clean.
*   **Use Case:** Integrating `mcp_efu` with another application on the same machine. For example, a parent Node.js or Python script could launch and communicate with this server to get file lists without using network sockets.
*   **Example:**
    ```bash
    python -m servers.mcp_efu.mcp_efu.main --transport stdio
    ```

### 3. TCP Server Mode

This mode runs `mcp_efu` as a persistent network server that listens for connections on a TCP socket.

*   **Function:** Listens for JSON-RPC 2.0 requests on a specified network port and sends responses back over the same socket. All log messages are sent to `stderr`.
*   **Use Case:** Allowing applications on a local or remote network to connect and request file lists. This is the most flexible option for building a distributed system where a central application needs to query file information from multiple machines.
*   **Example:**
    ```bash
    python -m servers.mcp_efu.mcp_efu.main --transport tcp --host 0.0.0.0 --port 8989
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
poetry run python -m unittest
```

This command uses Poetry to execute the test runner within the project's managed virtual environment. It will automatically discover and run all tests.

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

4.  **Running the tool**:
    After installation, the `mcp_efu` command is available within Poetry's virtual environment. You can run it using `poetry run` or by activating the virtual environment with `poetry shell`.
    ```bash
    # Run the tool via the defined script entry point
    poetry run mcp_efu --help

    # You can also run it as a module
    poetry run python -m mcp_efu.main --help

    # Alternatively, spawn a new shell first
    poetry shell
    (mcp_efu-py3.12) $ mcp_efu --help
    ```