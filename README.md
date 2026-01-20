# mcp.moukaeritai.work

This repository is for developing various MCP (Minecraft Proxy) servers.

## Directory Structure

All server projects are located within the `servers` directory. Each server is managed as an independent Python project.

```
mcp.moukaeritai.work/
├── servers/
│   ├── simple_proxy_server/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── requirements.txt
│   └── custom_lobby_server/
│       ├── __init__.py
│       ├── main.py
│       └── requirements.txt
├── .gitignore
└── README.md
```

## How to Add a New Server

To create a new server, follow these steps:

1.  **Create a new directory under `servers`**:
    ```bash
    mkdir servers/my_new_server
    ```

2.  **Create your Python files**:
    Create your main script (e.g., `main.py`), an `__init__.py`, and other necessary files inside the new directory.

3.  **Manage dependencies**:
    Create a `requirements.txt` file to list the Python libraries your server depends on.
    ```bash
    touch servers/my_new_server/requirements.txt
    ```

This structure allows each server to have its own dependencies and be developed independently.
