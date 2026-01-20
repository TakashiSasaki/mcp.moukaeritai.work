# mcp_efu/main.py
import argparse
import sys
import json
import os
from .core import EfuFileManager
from fastmcp import FastMCP

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
  python -m mcp_efu --transport stdio

  # Run as a one-off command to scan a directory and print JSON
  python -m mcp_efu ./my_directory

  # Scan a directory and write the output to a file
  python -m mcp_efu ./my_directory --output my_file_list.json
"""
    )

    # Server mode arguments
    server_group = parser.add_argument_group('Server Mode Arguments')
    server_group.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
        help="Run as an MCP server with the specified transport.\nstdio: Use standard input/output.\nsse: Use Server-Sent Events.\nstreamable-http: Use streamable HTTP."
    )

    # CLI mode arguments
    cli_group = parser.add_argument_group('CLI Mode Arguments')
    cli_group.add_argument(
        "path",
        nargs="?",  # Optional positional argument
        default=None,
        help="The path to scan. If provided, the tool runs as a one-off CLI command."
    )
    cli_group.add_argument(
        "-o", "--output",
        metavar="FILE",
        default=None,
        help="Write output to a file instead of stdout."
    )
    cli_group.add_argument(
        "--format",
        choices=["json"],  # Add more formats like 'csv' in the future
        default="json",
        help="Output format (default: json)."
    )


    args = parser.parse_args()

    # --- Mode selection ---
    if args.transport:
        # --- Server Mode ---
        if args.path:
            parser.error("Positional argument 'path' cannot be used with --transport. For server mode, path is provided in the JSONRPC request.")

        efu_manager = EfuFileManager()
        server = FastMCP(name="EFU File Lister", version="0.1.0")

        @server.tool(description="指定されたパス内のファイルとディレクトリの一覧を取得します。日時は常にWindowsのFILETIME 64ビット整数で返します。")
        def get_file_list(path: str) -> list[dict]:
            return efu_manager.get_file_list(path)

        @server.tool(description="指定されたフルパスのファイルのMD5ハッシュを取得します。戻り値のpathは絶対パス、realpathは実体パスです。")
        def get_md5_hash(path: str) -> dict:
            return efu_manager.get_md5_hash(path)

        @server.tool(description="指定されたフルパスのファイルのSHA1ハッシュを取得します。戻り値のpathは絶対パス、realpathは実体パスです。")
        def get_sha1_hash(path: str) -> dict:
            return efu_manager.get_sha1_hash(path)

        @server.tool(description="指定されたフルパスのファイルのGit Blob SHA1ハッシュを取得します。戻り値のpathは絶対パス、realpathは実体パスです。")
        def get_git_blob_hash(path: str) -> dict:
            return efu_manager.get_git_blob_hash(path)

        print(f"Starting MCP server with transport: {args.transport}", file=sys.stderr)
        try:
            server.run(transport=args.transport)
        except KeyboardInterrupt:
            print("\nServer shutting down gracefully.", file=sys.stderr)
        except Exception as e:
            print(f"\nAn unexpected server error occurred: {e}", file=sys.stderr)
    
    elif args.path:
        # --- CLI Mode ---
        efu_manager = EfuFileManager()
        print(f"Running in CLI mode to scan path: {args.path}", file=sys.stderr)
        try:
            file_list = efu_manager.get_file_list(args.path)
            
            # Handle output format
            if args.format == "json":
                output_data = json.dumps(file_list, indent=2)
            else:
                # This part is for future formats
                print(f"Error: Unsupported format '{args.format}'", file=sys.stderr)
                sys.exit(1)

            # Handle output destination
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_data)
                    f.write('\n')
                print(f"Output successfully written to {args.output}", file=sys.stderr)
            else:
                # Write to stdout
                sys.stdout.write(output_data)
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
