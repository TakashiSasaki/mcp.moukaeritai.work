import argparse
from quarry.net.proxy import Proxy, DownstreamFactory

# This defines the proxy server that will sit between the client and the upstream server.
# We can add custom logic here later to modify packets.
class SimpleProxy(Proxy):
    pass

# This factory creates instances of our SimpleProxy.
class SimpleProxyFactory(DownstreamFactory):
    proxy_class = SimpleProxy
    # We set a high protocol_version to support a wide range of client versions.
    protocol_version = 999

def main():
    # Set up command-line arguments to make the proxy configurable
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--listen-host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("-p", "--listen-port", default=25565, type=int, help="Port to listen on (default: 25565)")
    parser.add_argument("-b", "--connect-host", required=True, help="Host of the upstream Minecraft server to connect to")
    parser.add_argument("-q", "--connect-port", default=25565, type=int, help="Port of the upstream Minecraft server (default: 25565)")
    args = parser.parse_args()

    # Create the factory for our proxy
    factory = SimpleProxyFactory(args.connect_host, args.connect_port)

    # Start listening for connections
    factory.listen(args.listen_host, args.listen_port)

    print(f"MCP server proxy started!")
    print(f" >> Listening for clients on {args.listen_host}:{args.listen_port}")
    print(f" >> Forwarding connections to {args.connect_host}:{args.connect_port}")
    print("Press Ctrl+C to stop.")

if __name__ == "__main__":
    main()
