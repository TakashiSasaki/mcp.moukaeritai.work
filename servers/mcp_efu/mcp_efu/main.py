# mcp_efu/main.py
import argparse
import asyncio
import os
import sys
from .core import FileSystemManager
from .transport import start_tcp_server, start_stdio_server

def main():
    """
    The main entry point for the mcp_efu server.
    Parses command-line arguments and starts the server in the specified mode.
    """
    parser = argparse.ArgumentParser(
        description="mcp_efu: A server to list files over TCP or stdio.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--mode",
        choices=["stdio", "tcp"],
        default="tcp",
        help="The transport mode to use.\n"
             "stdio: Use standard input/output for communication.\n"
             "tcp: Use a TCP socket for communication (default)."
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for TCP server to listen on (default: localhost)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8989,
        help="Port for TCP server to listen on (default: 8989)."
    )
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help="The root directory to serve files from (default: current working directory)."
    )
    args = parser.parse_args()

    try:
        print(f"Initializing FileSystemManager with root: {args.root}", file=sys.stderr)
        fs_manager = FileSystemManager(args.root)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    main_coroutine = None
    if args.mode == "stdio":
        main_coroutine = start_stdio_server(fs_manager)
    elif args.mode == "tcp":
        main_coroutine = start_tcp_server(args.host, args.port, fs_manager)

    if main_coroutine:
        try:
            asyncio.run(main_coroutine)
        except KeyboardInterrupt:
            print("\nServer shutting down gracefully.", file=sys.stderr)
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
