# Simple Proxy Server

This is a basic Minecraft proxy server built with Python and the `quarry` library. It forwards connections from a client to a specified upstream Minecraft server.

## Setup

1.  **Navigate to the server directory**:
    ```bash
    cd servers/simple_proxy_server
    ```

2.  **Install dependencies**:
    It's recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install the required libraries
    pip install -r requirements.txt
    ```

## How to Run

Run the `main.py` script, specifying the host of the upstream Minecraft server you want to connect to.

```bash
python main.py --connect-host <upstream_server_host>
```

### Examples

-   **Forward to a server running on the same machine on port 25566**:
    ```bash
    python main.py --connect-host localhost --connect-port 25566
    ```
    You would then connect your Minecraft client to `localhost:25565`.

-   **Forward to a remote server**:
    ```bash
    python main.py --connect-host mc.example.com
    ```
    You would then connect your Minecraft client to `localhost:25565` (or whatever your machine's IP is).

### Command-Line Arguments

-   `--listen-host`: The IP address for the proxy to listen on. (Default: `0.0.0.0`)
-   `--listen-port`: The port for the proxy to listen on. (Default: `25565`)
-   `--connect-host`: **(Required)** The hostname or IP address of the upstream Minecraft server.
-   `--connect-port`: The port of the upstream Minecraft server. (Default: `25565`)
