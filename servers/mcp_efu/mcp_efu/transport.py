# mcp_efu/transport.py
import asyncio
import sys
import json
import time
from .core import EfuFileManager

def create_success_response(req_id, result):
    """Creates a JSON-RPC 2.0 success response."""
    return {"id": req_id, "result": result, "jsonrpc": "2.0"}

def create_error_response(req_id, code, message):
    """Creates a JSON-RPC 2.0 error response."""
    return {
        "id": req_id,
        "error": {"code": code, "message": message},
        "jsonrpc": "2.0"
    }

def extract_path_param(params):
    if isinstance(params, list) and len(params) == 1 and isinstance(params[0], str):
        return params[0]
    if isinstance(params, dict) and isinstance(params.get("path"), str):
        return params.get("path")
    return None

async def handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    efu_manager: EfuFileManager,
    peer_name: str
):
    """
    Generic handler for a connection (TCP or stdio).
    It reads line-by-line JSON-RPC requests and writes back JSON-RPC responses.
    """
    print(f"[{time.time()}] Connection established from {peer_name}", file=sys.stderr)
    try:
        # Define the tools provided by this server
        tools = [
            {
                "name": "get_file_list",
                "description": "指定されたパス内のファイルとディレクトリの一覧を取得します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "スキャンするルートパス"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_md5_hash",
                "description": "指定されたフルパスのファイルのMD5ハッシュを取得します。戻り値のpathは絶対パス、realpathは実体パスです。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "ハッシュを計算するファイルのフルパス"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_sha1_hash",
                "description": "指定されたフルパスのファイルのSHA1ハッシュを取得します。戻り値のpathは絶対パス、realpathは実体パスです。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "ハッシュを計算するファイルのフルパス"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_git_blob_hash",
                "description": "指定されたフルパスのファイルのGit Blob SHA1ハッシュを取得します。戻り値のpathは絶対パス、realpathは実体パスです。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "ハッシュを計算するファイルのフルパス"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]

        # Send server/hello notification upon connection
        hello_notification = {
            "jsonrpc": "2.0",
            "method": "server/hello",
            "params": {
                "version": "0.1.0",
                "displayName": "EFU File Lister",
                "tools": tools
            }
        }
        print(f"[{time.time()}] RSP < {hello_notification}", file=sys.stderr)
        writer.write((json.dumps(hello_notification) + '\n').encode())
        await writer.drain()

        while not reader.at_eof():
            request_line = await reader.readline()
            if not request_line:
                continue

            request_str = request_line.decode().strip()
            if not request_str:
                continue
            
            print(f"[{time.time()}] RAW < {request_str}", file=sys.stderr)

            req_id = None
            try:
                request = json.loads(request_str)
                print(f"[{time.time()}] REQ > {request}", file=sys.stderr)

                req_id = request.get("id")
                method = request.get("method")
                params = request.get("params")

                if method == "tools/list":
                    response = create_success_response(req_id, {"tools": tools})

                elif method == "get_file_list":
                    path = extract_path_param(params)
                    if path is not None:
                        try:
                            file_list = efu_manager.get_file_list(path)
                            response = create_success_response(req_id, file_list)
                        except ValueError as e:
                            response = create_error_response(req_id, -32000, f"Server error: {e}")
                    else:
                        response = create_error_response(req_id, -32602, "Invalid params: Expected a list with one string [path] or an object {'path': '...'}.")
                elif method == "get_md5_hash":
                    path = extract_path_param(params)
                    if path is not None:
                        try:
                            result = efu_manager.get_md5_hash(path)
                            response = create_success_response(req_id, result)
                        except ValueError as e:
                            response = create_error_response(req_id, -32000, f"Server error: {e}")
                    else:
                        response = create_error_response(req_id, -32602, "Invalid params: Expected a list with one string [path] or an object {'path': '...'}.")
                elif method == "get_sha1_hash":
                    path = extract_path_param(params)
                    if path is not None:
                        try:
                            result = efu_manager.get_sha1_hash(path)
                            response = create_success_response(req_id, result)
                        except ValueError as e:
                            response = create_error_response(req_id, -32000, f"Server error: {e}")
                    else:
                        response = create_error_response(req_id, -32602, "Invalid params: Expected a list with one string [path] or an object {'path': '...'}.")
                elif method == "get_git_blob_hash":
                    path = extract_path_param(params)
                    if path is not None:
                        try:
                            result = efu_manager.get_git_blob_hash(path)
                            response = create_success_response(req_id, result)
                        except ValueError as e:
                            response = create_error_response(req_id, -32000, f"Server error: {e}")
                    else:
                        response = create_error_response(req_id, -32602, "Invalid params: Expected a list with one string [path] or an object {'path': '...'}.")
                else:
                    response = create_error_response(req_id, -32601, f"Method not found: {method}")

            except json.JSONDecodeError:
                response = create_error_response(req_id, -32700, "Parse error: Invalid JSON.")
            except Exception as e:
                response = create_error_response(req_id, -32603, f"Internal error: {e}")

            print(f"[{time.time()}] RSP < {response}", file=sys.stderr)
            writer.write((json.dumps(response) + '\n').encode())
            await writer.drain()

    except (asyncio.CancelledError, ConnectionResetError):
        pass  # Client disconnected
    except Exception as e:
        print(f"An unexpected error occurred with {peer_name}: {e}", file=sys.stderr)
    finally:
        print(f"Closing connection with {peer_name}", file=sys.stderr)
        if not writer.is_closing():
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass  # Ignore errors on close

async def start_tcp_server(host: str, port: int, efu_manager: EfuFileManager):
    """Starts the TCP server."""
    try:
        server = await asyncio.start_server(
            lambda r, w: handle_connection(r, w, efu_manager, f"TCP client {w.get_extra_info('peername')}"),
            host,
            port
        )
        addr = server.sockets[0].getsockname()
        print(f"TCP server listening on {addr}", file=sys.stderr)
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Failed to start TCP server: {e}", file=sys.stderr)


async def start_stdio_server(efu_manager: EfuFileManager):
    """Starts the stdio server, using stdin and stdout."""
    print("stdio server started. Waiting for JSON-RPC requests on stdin.", file=sys.stderr)
    loop = asyncio.get_running_loop()
    try:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)

        await handle_connection(reader, writer, efu_manager, "stdio")
    except Exception as e:
        print(f"Error in stdio server: {e}", file=sys.stderr)
