# mcp_efu

`mcp_efu` is a server and command-line tool that generates file lists in a format compatible with the Everything File List (EFU). It can run as an MCP server over stdio/SSE/streamable HTTP or as a one-off command.

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

This mode runs `mcp_efu` as an MCP server that communicates over `stdin` and `stdout`.

```bash
poetry run mcp_efu --transport stdio
```

Codex から利用する場合は、`~/.codex/config.toml` に次のように設定すると認識されます。

```toml
[mcp_servers.mcp_efu_stdio]
command = "poetry"
args = ["run", "mcp_efu", "--transport", "stdio"]
cwd = "/workspaces/mcp.moukaeritai.work/servers/mcp_efu"
```

Gemini Code Assist や Gemini CLI から利用する場合は、`~/.gemini/settings.json` に次のように設定すると認識されます。

```json
{
  "mcpServers": {
    "mcp_efu_stdio": {
      "command": "python",
      "args": [
        "-m",
        "mcp_efu",
        "--transport",
        "stdio"
      ],
      "cwd": "/workspaces/mcp.moukaeritai.work/servers/mcp_efu"
    }
  }
}
```

### 3. HTTP Server Modes

These modes run `mcp_efu` as an MCP server over HTTP.

```bash
# Server-Sent Events transport
poetry run mcp_efu --transport sse

# Streamable HTTP transport
poetry run mcp_efu --transport streamable-http
```

## MCP Tool

The MCP server exposes a single tool:

- `get_file_list(path: str)`: Returns the EFU-compatible file list for the given path.

See `METHODS.md` for a human-readable description of the tool, inputs, and outputs.

## Testing

This project uses Python's built-in `unittest` framework. Tests are located in the `tests/` directory.

To run the automated tests, first ensure you are in the project's root directory (`servers/mcp_efu`), then use the following command:

```bash
# Ensure you are in /path/to/servers/mcp_efu
poetry run python -m unittest discover
```

This command uses Poetry to execute the test runner within the project's managed virtual environment. It will automatically discover and run all tests.
