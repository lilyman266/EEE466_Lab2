import os.path as path
import sys

from comm_interface import CommInterfaceFactory
from udp_filetransfer import UDPFileTransfer


def main():
    """
    Server instantiates a UDP communication interface.
    
    Commands:
        PUT <filename>: The server receives a file from the client and saves it
                        to the `ServerFS/download/` directory.
        GET <filename>: The server sends a file from the `ServerFS/upload/`
                        directory to the client.
        QUT: The server prints a shutdown message and exits gracefully.
        ERR <message>: The server prints an error message sent by a client.
    """
    server = CommInterfaceFactory.create(
        UDPFileTransfer, is_server=True, host="0.0.0.0", port=9001
    )
    print("Server is listening for commands...")

    while True:
        command, filename, client_addr = server.receive_message()
        print(f"Server received {command} {filename}")
        server.socket.settimeout(0.2)

        if command.upper() == "PUT":
            filepath = path.join("ServerFS", "download", f"{filename}")
            server.receive_file(filepath)

        elif command.upper() == "GET":
            filepath = path.join("ServerFS", "upload", f"{filename}")
            server.send_file(filepath, client_addr)

        elif command.upper() == "QUT":
            print("Shutting down.")
            sys.exit(0)

        elif command.upper() == "ERR":
            print(f"Server received the following error message:\n{filename}")

        else:
            print(
                f"Unknown command received.\n{command}:{filename} received from {client_addr}"
            )


if __name__ == "__main__":
    main()
