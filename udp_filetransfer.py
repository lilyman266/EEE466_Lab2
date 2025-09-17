import os
import random
import socket
import time

from comm_interface import CommInterface

random.seed(1)
DROP_PROBABILITY = 0.0
DUPLICATE_PROBABILITY = 0.0
LAG_PROBABILITY = 0.0

CHUNK_SIZE = 1024

class UDPFileTransfer(CommInterface):
    """Reliable UDP file transfer implementation."""

    CHUNK_SIZE = 1024

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def initialize_as_server(self, host, port):
        pass

    def initialize_as_client(self):
        pass

    def _send(self, message, dest_addr):
        if random.random() < DROP_PROBABILITY:
            return
        if random.random() < DUPLICATE_PROBABILITY:
            self.socket.sendto(message, dest_addr)
        if random.random() < LAG_PROBABILITY:
            time.sleep(random.uniform(0.1, 0.3))

        self.socket.sendto(message, dest_addr)


    def send_message(self, data, parameters="", addr=None):
        pass

    def send_file(self, filepath, addr):
        pass

    def receive_message(self):
        pass

    def receive_file(self, filepath):
        pass
