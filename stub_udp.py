import os
import random
import socket
import time
import sys

from comm_interface import CommInterface

random.seed(1)
DROP_PROBABILITY = 0
DUPLICATE_PROBABILITY = 0
LAG_PROBABILITY = 1

"""DROP PROBABILITY:
This is an issue because you want every command to be executed. in order. Each 
command needs a number which increments every time, and if the server receives a
command that skips a number, it should request that number again.

DUPLICATE PROBABILITY:
If a command is executed twice, it won't actually affect anything. The worst 
case scenario is that a file is sent twice, which is not a big deal.

LAG PROBABILITY: 
Lag in a packet could make the packet come later than a later packet. This can 
be solved by banking the received packet and executing it when the missing 
packet is received.

1) Send packets and increment their number each time.
2) If a packet is received out of order, store it in a dictionary with the
   packet number as the key.
3) If a packet is missing, request it again.
4) Execute packets in order."""

CHUNK_SIZE = 1024

class UDPFileTransfer(CommInterface):
    """Reliable UDP file transfer implementation."""

    CHUNK_SIZE = 1024

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_number = 0
        self.send_number = 0

    def initialize_as_server(self, host, port):
        self.socket.bind((host, port))
        self.socket.settimeout(5)

    def initialize_as_client(self):
        self.socket.settimeout(5)

    def _send(self, message, dest_addr):
        if random.random() < DROP_PROBABILITY:
            print("DROPPED!")
            return
        if random.random() < DUPLICATE_PROBABILITY:
            print("DOUBLE!")
            self.socket.sendto(message, dest_addr)
        if random.random() < LAG_PROBABILITY:
            print("LAG!")
            time.sleep(random.uniform(0.1, 0.3))

        self.socket.sendto(message, dest_addr)


    def send_message(self, data, param="", addr=None):
        to_send = f"{self.send_number}:{data}:{param}"
        self.send_number += 1
        #send message and wait for ACK. If ACK doesn't come in 1 second, resend 
        # message.
        while 1:
            print("send attempt")
            self.socket.sendto(to_send.encode(encoding="utf8"), addr)
            try:
                message, server_addr = self.socket.recvfrom(1024)
                break
            except socket.timeout:
                print(f"Timeout, resending packet number: {to_send.split(':')[0]}")
            except ConnectionResetError:
                print(f"Packet {self.send_number-1} received a connection closed. Shutting down...")
                sys.exit(0)
                
        if message.decode().split(":")[1] == "ACK":
            print(f"Packet number {to_send.split(':')[0]} acknowledged by server")

    def send_file(self, filepath, addr):
        pass

    def receive_message(self):
        while 1:
            try: 
                message, client_addr = self.socket.recvfrom(1024)
                break
            except socket.timeout:
                print("Socket timed out. Trying again...")
        number = message.decode().split(":")[0]
        command = message.decode().split(":")[1]
        filename = message.decode().split(":")[2]
        #do operations with number
        #if packet is out of order, request again. Otherwise, send ACK
        if int(number) > self.recv_number:
            print(f"Packet {number} received out of order, requesting again")
            self.send_message("ERR", param=f"Packet {number} missing", addr=client_addr)
            return self.receive_message()
        self.recv_number += 1
        print(f"Received packet number: {number}. Current tally is {self.recv_number}")
        if command != "QUT":
            self.send_message("ACK", addr=client_addr)
            print("ACK sent!")
        return command, filename, client_addr

    def receive_file(self, filepath):
        pass