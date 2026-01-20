# mcp_efu/transport.py
import asyncio
import sys
import json
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
    print(f"Connection established from {peer_name}", file=sys.stderr)
    try:
        while not reader.at_eof():
            request_line = await reader.readline()
            if not request_line:
                continue

            request_str = request_line.decode().strip()
            if not request_str:
                continue

            req_id = None
            try:
                request = json.loads(request_str)
                req_id = request.get("id")
                method = request.get("method")
                params = request.get("params")

                if method == "get_file_list":
                    if not isinstance(params, list) or len(params) != 1 or not isinstance(params[0], str):
                        response = create_error_response(req_id, -32602, "Invalid params: Expected a list with one string [path].")
                    else:
                        root_path = params[0]
                        try:
                            file_list = efu_manager.get_file_list(root_path)
                            response = create_success_response(req_id, file_list)
                        except ValueError as e:
                            response = create_error_response(req_id, -32000, f"Server error: {e}")
                else:
                    response = create_error_response(req_id, -32601, f"Method not found: {method}")

            except json.JSONDecodeError:
                response = create_error_response(req_id, -32700, "Parse error: Invalid JSON.")
            except Exception as e:
                response = create_error_response(req_id, -32603, f"Internal error: {e}")

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