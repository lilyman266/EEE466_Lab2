import os
import random
import socket
import time
import sys

from comm_interface import CommInterface

random.seed(1)
DROP_PROBABILITY = 0
DUPLICATE_PROBABILITY = 0.1
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

CHUNK_SIZE = 1024

class UDPFileTransfer(CommInterface):
    """Reliable UDP file transfer implementation."""

    CHUNK_SIZE = 1024

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_seq = 0
        self.recv_seq = -1
        self.client_addr = None
        self.sent_messages = {}

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

    #command = GET data = file stuff
    def send_message(self, command, data=None, seq=None, param="", addr=None):
        if seq is None:
            seq = self.send_seq
        #1) Take a chunk, format it with a "Syn" ||| "Type" ||| "Data"
        if param != "":
            data = param.encode()
        # to_send = f"{seq}|||{command}|||{data}"
        to_send = f"{seq}|||{command}|||"
        print(f"Message to send: {to_send}")
        #2) encode
        if data:
            to_send = to_send.encode() + data
        else:
            to_send = to_send.encode()
        print(f"Encoded message to send: {to_send}")
        #3) loop
        #4)     send file
        #5)     wait until timeout (resend!) or until ack
        while True:
            try:
                #1) Append "sent file" to log#
                self._send(to_send, addr)
                print(f"message sent!")

                message, _ = self.socket.recvfrom(self.CHUNK_SIZE)
                message = message.decode()
                #split the message
                split_message = message.split("|||")
                #find the syn and type
                seq_ack = int(split_message[0])
                type_ack = split_message[1]
                #if the syn is the same, break
                if seq_ack == seq and type_ack == "ACK":
                    print(f"ACK received!")
                    break
                hopeful_ack = self.receive_message()
                print(f"ack message received: {hopeful_ack}")
                # (if hopeful_ack[2] == "Ack" etc)
                break
            except TimeoutError:
                pass
        self.send_seq += 1
        #6) up seq number
        # to_send = f"{self.send_number}:{data}:{param}"
        # self.send_number += 1
        # #send message and wait for ACK. If ACK doesn't come in 1 second, resend
        # # message.
        # while 1:
        #     print("send attempt")
        #     self.socket.sendto(to_send.encode(encoding="utf8"), addr)
        #     try:
        #         message, server_addr = self.socket.recvfrom(1024)
        #         break
        #     except socket.timeout:
        #         print(f"Timeout, resending packet number: {to_send.split(':')[0]}")
        #     except ConnectionResetError:
        #         print(f"Packet {self.send_number-1} received a connection closed. Shutting down...")
        #         sys.exit(0)
        #
        # if message.decode().split(":")[1] == "ACK":
        #     print(f"Packet number {to_send.split(':')[0]} acknowledged by server")

    def send_file(self, filepath, addr):
        pass
        # 1) take the filepath and read(rb) CHUNK_SIZE chunks from it, passing them to send_message.
        with open(filepath, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE-50):
                self.send_message("FILE", data=chunk, addr=addr)
            self.send_message("EOF", data=b"", addr=addr)

    def receive_message(self):
        #1) try to receive chunk (timeout just loop)
        while True:
            try:
                received_chunk, self.client_addr = self.socket.recvfrom(self.CHUNK_SIZE)
                received_chunk = received_chunk
                msg_syn, msg_type, msg_info = received_chunk.split(b"|||")


                print(f"next message received! seq_type: {msg_type}, type_ack: {msg_syn}, msg_info: {msg_info}")
                #send ack message with _send if it is the next message to send
                if int(msg_syn) == self.recv_seq + 1:
                    self.recv_seq += 1
                    to_send = f"{self.recv_seq}|||ACK|||".encode()
                    self._send(to_send, dest_addr=self.client_addr)
                    print("returning")
                    if msg_type != b"FILE" and msg_type != b"EOF":
                        return msg_type.decode(), msg_info.decode(), self.client_addr
                    else:
                        return msg_type, msg_info, self.client_addr
                else:
                    to_send_dropped = f"{self.recv_seq}|||ACK|||".encode()
                    self._send(to_send_dropped, dest_addr=self.client_addr)

                # message, _ = self.socket.recvfrom(CHUNK_SIZE)
                # message = message.decode()
                # # split the message
                # split_message = message.split("|||")
                # # find the syn and type
                # seq_ack = int(split_message[0])
                # type_ack = split_message[1]
                # print(f"next message received! seq_ack: {seq_ack}, type_ack: {type_ack}")
                # if the syn is the same, break
                # if seq_ack > self.recv_seq:
                #     print(f"next message received!")
                #     break
                # 2) on receive, send "Syn = Syn (recv)" ||| "Type = Ack" ||| "Data = """ and wait for the next send. if Syn is higher than previous syn, then keep going
                # print(int(msg_syn))
                # 3) decode
                # 4) return msg.split("|||") (list!!!)
            except TimeoutError:
                print("wtf")
                continue
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
        # if int(number) > self.recv_number:
        #     print(f"Packet {number} received out of order, requesting again")
        #     self.send_message("ERR", param=f"Packet {number} missing", addr=client_addr)
        #     return self.receive_message()
        # self.recv_number += 1
        # print(f"Received packet number: {number}. Current tally is {self.recv_number}")
        # if command != "QUT":
        #     self.send_message("ACK", addr=client_addr)
        #     print("ACK sent!")
        # return command, filename, client_addr

    def receive_file(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        #1) open path to write(wb) to
        with open(filepath, "wb") as f:
        #2)     write message to file
            while True:
                msg_type, msg_info, self.client_addr = self.receive_message()
                if msg_type == b"FILE":
                    f.write(msg_info)
                elif msg_type == b"EOF":
                    break
                else:
                    print(f"unknown command {msg_type}")
        #3)
