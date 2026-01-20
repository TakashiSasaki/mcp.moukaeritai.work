# mcp_efu/main.py
import argparse
import asyncio
import sys
import json
import os
from .core import EfuFileManager
from .transport import start_tcp_server, start_stdio_server

def main():
    """
    The main entry point for the mcp_efu application.
    Can run as an MCP server or as a one-off CLI tool.
    """
    # Print current working directory at the beginning
    print(f"Current working directory: {os.getcwd()}", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="mcp_efu: A tool to generate EFU file lists. Can run as a server or a single-command CLI.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  # Run as a stdio server
  python -m servers.mcp_efu.mcp_efu.main --transport stdio

  # Run as a one-off command to scan a directory and print JSON
  python -m servers.mcp_efu.mcp_efu.main ./my_directory
"""
    )

    # Server mode arguments
    parser.add_argument(
        "--transport",
        choices=["stdio", "tcp"],
        default=None,
        help="Run as a server with the specified transport.\n             stdio: Use standard input/output for communication.\n             tcp: Use a TCP socket for communication."
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

    # CLI mode argument
    parser.add_argument(
        "path",
        nargs="?",  # Optional positional argument
        default=None,
        help="The path to scan. If provided, the tool runs as a one-off CLI command."
    )

    args = parser.parse_args()

    efu_manager = EfuFileManager()

    # --- Mode selection ---
    if args.transport:
        # --- Server Mode ---
        print(f"Starting server with transport: {args.transport}", file=sys.stderr)
        main_coroutine = None
        if args.transport == "stdio":
            main_coroutine = start_stdio_server(efu_manager)
        elif args.transport == "tcp":
            main_coroutine = start_tcp_server(args.host, args.port, efu_manager)

        if main_coroutine:
            try:
                asyncio.run(main_coroutine)
            except KeyboardInterrupt:
                print("\nServer shutting down gracefully.", file=sys.stderr)
            except Exception as e:
                print(f"\nAn unexpected server error occurred: {e}", file=sys.stderr)
    
    elif args.path:
        # --- CLI Mode ---
        print(f"Running in CLI mode to scan path: {args.path}", file=sys.stderr)
        try:
            file_list = efu_manager.get_file_list(args.path)
            # Pretty-print the JSON result to stdout
            sys.stdout.write(json.dumps(file_list, indent=2))
            sys.stdout.write('\n')
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # --- No valid mode selected ---
        print("\nNo command or server transport specified. See --help for options.", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()