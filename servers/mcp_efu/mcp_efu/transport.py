# mcp_efu/transport.py
import asyncio
import sys
from .core import FileSystemManager

async def handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    fs_manager: FileSystemManager,
    peer_name: str
):
    """
    Generic handler for a connection (TCP or stdio).
    It reads line-by-line JSON requests and writes back JSON responses.
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

            # Log the request for debugging
            # print(f"Received from {peer_name}: {request_str}", file=sys.stderr)

            response_str = await fs_manager.handle_request(request_str)

            # Log the response for debugging
            # print(f"Sending to {peer_name}: {response_str.strip()}", file=sys.stderr)

            writer.write(response_str.encode())
            await writer.drain()
    except (asyncio.CancelledError, ConnectionResetError):
        # Handle client disconnection gracefully
        pass
    except Exception as e:
        print(f"An error occurred with {peer_name}: {e}", file=sys.stderr)
    finally:
        print(f"Closing connection with {peer_name}", file=sys.stderr)
        if not writer.is_closing():
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"Error closing writer for {peer_name}: {e}", file=sys.stderr)

async def start_tcp_server(host: str, port: int, fs_manager: FileSystemManager):
    """Starts the TCP server."""
    try:
        server = await asyncio.start_server(
            lambda r, w: handle_connection(r, w, fs_manager, f"TCP client {w.get_extra_info('peername')}"),
            host,
            port
        )
        addr = server.sockets[0].getsockname()
        print(f"TCP server listening on {addr}", file=sys.stderr)
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Failed to start TCP server: {e}", file=sys.stderr)


async def start_stdio_server(fs_manager: FileSystemManager):
    """Starts the stdio server, using stdin and stdout."""
    print("stdio server started. Waiting for JSON requests on stdin.", file=sys.stderr)
    loop = asyncio.get_running_loop()

    try:
        # Create streams for stdin
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        # Create streams for stdout
        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)

        # Use the generic handler for stdio
        await handle_connection(reader, writer, fs_manager, "stdio")
    except Exception as e:
        print(f"Error in stdio server: {e}", file=sys.stderr)
