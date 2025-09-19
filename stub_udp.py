import os
import random
import socket
import time
import sys

from comm_interface import CommInterface

random.seed(1)
DROP_PROBABILITY = 0
DUPLICATE_PROBABILITY = 0
LAG_PROBABILITY = 0

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

#TCKMS
# Don't need to do a handshake because the synchronization numbers are 0 and 1000
# Every message is acked with a flag or its own ack message. 
# Every message has a FIN flag - if this is set, no reply is expected.
# Every message has a sequence number - makes every message unique (even duplicates)

# RULES
# 1) If a message is received, send an ack.
# 2) Do not send the next message until you receive an ack
# 3) If you don't receive an ack within timeout time, resend message
# 4) If you receive an ack, and you have data to send, send an ack with the data in the same packet.
# 5) If you receive a message with a syn number that you have seen before, drop it (handles duplicates)
# 6) If you receive a message with a FIN in it, ack then shut down.

#x y ack fin data addr

CHUNK_SIZE = 1024

class UDPFileTransfer(CommInterface):
    """Reliable UDP file transfer implementation."""

    CHUNK_SIZE = 1024

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq_y = 0
        self.seq_x = 0
        self.future_ack = False
        self.ack = False
        self.fin = False

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

    def send_message(self, data, param="", addr=None, qut=False):
        #Do the operations
        #Package the data
        #send the thang
        #call receive
        #if receive times out, then repeat step 3 and continue

        #Step 1: Do the operations
        # seq_x: increments after sending a packet
        # seq_y: increments after receiving a packet
        # fin: If QUT was received, set to 1
        # ack: If "future ack" flag set, set to 1. If message was received, set to 1.
        # data: contains data which can do anything you can imagine
        # Param: We don't talk about him

        if qut:
            self.fin = True
        if self.future_ack:
            self.ack = True

        to_send = f"{self.seq_x}:{self.seq_y}:{self.ack}:{self.fin}:{data}:{param}"

        while 1:
            self._send(to_send, addr)

            try:
                command, filename, client_addr = self.receive_message()
                break
            except socket.timeout:
                continue

        # #send message and wait for ACK. If ACK doesn't come in 1 second, resend
        # # message.
        # while data != "ACk":
        #     print("send attempt")
        #     self.seq_x += 1
        #     self._send(to_send.encode(encoding="utf8"), addr)
        #     try:
        #         message, server_addr = self.socket.recvfrom(1024)
        #         break
        #     except socket.timeout:
        #         print(f"Timeout, resending packet number: {to_send.split(':')[0]}")
        #         self.seq_x -= 1
        #     except ConnectionResetError:
        #         print(f"Packet {self.seq_x-1} received a connection closed. Shutting down...")
        #         sys.exit(0)
        #
        # if message.decode().split(":")[1] == "ACK":
        #     print(f"Packet number {to_send.split(':')[0]} acknowledged by server")

    def send_file(self, filepath, addr):
        pass

    def receive_message(self):
        #wait for a message (recvfrom)
        #if message contains data, send an ack. otherwise, set "future ack" flag to 1 , so that the next message we send can have the ack flag set
        #parse data and do thing




        # while 1:
        #     try:
        #         message, client_addr = self.socket.recvfrom(1024)
        #         break
        #     except socket.timeout:
        #         print("Socket timed out. Trying again...")
        # number = message.decode().split(":")[0]
        # command = message.decode().split(":")[1]
        # filename = message.decode().split(":")[2]
        # #do operations with number
        # #if packet is out of order, request again. Otherwise, send ACK
        #
        # #drop repeat packets
        # if int(number) >= self.seq_y:
        #     print(f"Packet {number} received twice, dropping packet")
        #     self.seq_y -= 1
        #     #return self.receive_message()
        #
        # self.seq_y += 1
        # print(f"Received packet number: {number}. Current tally is {self.seq_y}")
        # if command != "QUT":
        #     self.send_message("ACK", addr=client_addr)
        #     print("ACK sent!")
        # return command, filename, client_addr
        pass

    def receive_file(self, filepath):
        pass
