import json
import os.path as path
import sys

from comm_interface import CommInterfaceFactory
from stub_udp import UDPFileTransfer


def main():
    """
    Client instantiates a UDP communication interface. It reads commands from
    "work_order.json".

    Commands processed from "work_order.json":
        PUT <filename>: The client sends a file from the `ClientFS/upload/`
                        directory to the server.
        GET <filename>: The client requests a file from the server and saves
                        it to the `ClientFS/download/` directory.
        QUT: The client sends a quit command to the server and exits.
    """
    client = CommInterfaceFactory.create(UDPFileTransfer)
    client.socket.settimeout(0.2)
    server_addr = ('127.0.0.1', 9001)
    

    # Load the JSON file
    with open("work_order.json", "r") as file:
        work_order_entries = json.load(file)

    # For each top-level entry, parse and send request to the server
    for entry in work_order_entries:
        command, filename = entry["command"], entry["filename"]
        print(f"Client sending {command} {filename}")

        if command.upper() == "PUT":
            client.send_message(command, param=filename, addr=server_addr)
            filepath = path.join("ClientFS", "upload", f"{filename}")
            client.send_file(filepath, server_addr)

        elif command.upper() == "GET":
            client.send_message(command, param=filename, addr=server_addr)
            filepath = path.join("ClientFS", "download", f"{filename}")
            client.receive_file(filepath)

        elif command.upper() == "QUT":
            client.send_message(command, addr=server_addr)
            print("Shutting down.")
            sys.exit(0)

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
