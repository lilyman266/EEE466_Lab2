import os
import random
import socket
import time
import sys

from comm_interface import CommInterface

random.seed(5)
DROP_PROBABILITY = 0.1
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

CHUNK_SIZE = 1024

class UDPFileTransfer(CommInterface):
    """Reliable UDP file transfer implementation."""

    CHUNK_SIZE = 1024

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_seq = 0
        self.recv_seq = -1
        self.client_addr = None
        self.sent_messages = []

    def initialize_as_server(self, host, port):
        self.socket.bind((host, port))
        self.socket.settimeout(5)

    def initialize_as_client(self):
        self.socket.settimeout(5)

    def _send(self, message, dest_addr):
        if message.split(b"|||")[1].decode() != "ACK":
            self.sent_messages.append(message)
        
        print(f"Sending message: {message}")
        # Simulate unreliable network conditions
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

    #Send_message:
    # Parameters:
    #      self - enables acess to local attributes
    #      command - Determines the TYPE of message. In addition to the message types 
    #            in the starting code, there is ACK added which represents a packet 
    #            whose only purpose is to ack a previous packet, and FILE, which tells
    #            the receiver that the data within must be written to a file (whose
    #            path is defined by the GET or PUT request). Lastly there is an EOF
    #            message type, which signifies the end of a file, allowing for 
    #            execution to continue.
    #      data - file data, already encoded in bytes. 
    #      seq - integer which represents the sender's seqence number. This is used
    #            checked on receive, and put in the ack, so both sender stay 
    #            synchronized.
    #      param - command data, not encoded in bytes.
    #      addr - socket to send message to.
    # Returns:
    #      N/A
    # Description:
    #      This method sends a message reliably adhereing to a custom UDP File Transfer
    #      protocol made for this application. It first constructs the message based on
    #      the parameters it was given, then sends it. After the send, it waits for an
    #      ACK to be returned for that specific packet, and exits. If this does not 
    #      happen within the socket timeout time, the message gets sent again.
    def send_message(self, command, data=None, seq=None, param="", addr=None):
        #Firstly, the message builds the message based on the parameters it received.
        if seq is None:
            seq = self.send_seq
        #1) Take a chunk, format it with a "Syn" ||| "Type" ||| "Data"
        if param != "":
            data = param.encode()
        # to_send = f"{seq}|||{command}|||{data}"
        to_send = f"{seq}|||{command}|||"
        #2) encode
        if data:
            to_send = to_send.encode() + data
        else:
            to_send = to_send.encode()
        #next, the function increments its sequence number on the "send" side. This will
        #be used to coordinate messages.
        self.send_seq += 1
        while True:
            try:
                #1) send the message
                self._send(to_send, addr)
                # 2) Wait for an ACK. If it is a duplicate message, drop it. If it is not
                # an ack, the other side's ack must have been dropped. To re-coordinate,
                # resend your message. The other side will receive it as a duplicate,
                # resend the ack, and resend the message you just received. Sneaky break
                # should never be accessed. In testing, it was never accessed.
                message, _ = self.socket.recvfrom(self.CHUNK_SIZE)
                #split the message
                split_message = message.split(b"|||")
                #find the syn and type
                seq_ack = int(split_message[0].decode())
                type_ack = split_message[1].decode()
                #if the syn is the same, break
                if seq_ack == seq and type_ack == "ACK":
                    print(f"ACK received!")
                    self.sent_messages.pop()
                    break
                elif seq_ack < seq and type_ack == "ACK":
                    print(f"Duplicate ACK received, waiting for correct ACK. my seq: {self.send_seq}, ack seq: {seq_ack}, ack type: {type_ack}")
                    continue
                #if you receive something that isn't an ACK, resend the last thing
                elif type_ack != "ACK":
                    print(f"Ack from other side got dropped. my seq: {self.send_seq}, ack seq: {seq_ack}, ack type: {type_ack}")
                    to_send = f"{self.recv_seq}|||ACK|||".encode()
                    self._send(self.sent_messages[-1], dest_addr=self.client_addr)
                    continue

                print(f"Used the sneaky break... my seq: {self.send_seq}, ack seq: {seq_ack}, ack type: {type_ack}")
                break
            # If the socket times out, resend the packet.
            except TimeoutError:
                print(f"Timeout, resending packet number: {seq}")
                continue
    # Send File:
    # Parameters:
    #      self - enables acess to local attributes.
    #      filepath - filepath to read the file to be sent from.
    #      addr - socket to send to.
    # Returns:
    #      N/A
    # Description:
    #      Simply opens a file and reads it in chunks to be sent. The chunk size is based
    #      on the global variable CHUNK_SIZE, minus enough bytes for the packet header to 
    #      be added on, making a total packet size no greater than CHUNK_SIZE.
    def send_file(self, filepath, addr):
        pass
        # 1) take the filepath and read(rb) CHUNK_SIZE chunks from it, passing them to send_message.
        with open(filepath, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE-50):
                self.send_message("FILE", data=chunk, addr=addr)
            self.send_message("EOF", data=b"", addr=addr)
           
    # Receive Message:
    # Parameters:
    #      self - enables acess to local attributes.
    # Returns:
    #      msg_type - The type of the message received. This could be GET, PUT, QUT, DEL,
    #         ACK, FILE, or EOF.
    #      msg_info - The data that the message contained. This could either be file data
    #         or an instruction.
    #      self.client_addr - this is the address of the client. This is added to ensure
    #         functionality of both the client and server applications.
    # Description:
    #      This function is designed to reliable receive a message using a custom UDP File
    #      Transfer Protocol designed for this lab. It first tries to receive a message.
    #      If it does not receive a message in the socket timeout time, then it tries
    #      again. When it receives a message, it checks if that message is a duplicate.
    #      If it is, it droppes that message. Next, if the message is the message to be 
    #      received, then it sends an ACK message back. Lastly, it contains some return
    #      logic to account for the different implementations of instruction receiving
    #      and file chunk receiving.
    def receive_message(self):
        while True:
            try:
               #receive chunck
                received_chunk, self.client_addr = self.socket.recvfrom(self.CHUNK_SIZE)
                received_chunk = received_chunk
                msg_syn, msg_type, msg_info = received_chunk.split(b"|||")

                #compare syn to recv_syn. If it is alreadyh received, ignore content and resend ack
                
                #If the message is a duplicate, ignore content and resend ack
                if int(msg_syn) <= self.recv_seq:
                    print(f"Duplicate message received! msg_type: {msg_type}, msg_syn: {msg_syn}, my syn: {self.recv_seq}, msg_info: {msg_info}")
                    to_send_ack = f"{int(msg_syn)}|||ACK|||".encode()
                    self._send(to_send_ack, dest_addr=self.client_addr)
                    continue
                print(f"next message received! msg_type: {msg_type}, msg_syn: {msg_syn}, my syn: {self.recv_seq}, msg_info: {msg_info}")
                #send ack message with _send if it is the next message to send
                if int(msg_syn) == self.recv_seq + 1:
                    self.recv_seq += 1
                    to_send = f"{int(msg_syn)}|||ACK|||".encode()
                    self._send(to_send, dest_addr=self.client_addr)
                    print("returning")
                   # Return Logic
                    if msg_type != b"FILE" and msg_type != b"EOF":
                        return msg_type.decode(), msg_info.decode(), self.client_addr
                    else:
                        return msg_type, msg_info, self.client_addr

            except TimeoutError:
                print("Message Receive Timed out")
                continue
    # Receive File:
    # Parameters:
    #      self - enables acess to local attributes.
    #      filepath - filepath to write the file to be receives to.
    # Returns:
    #      N/A
    # Description:
    #      Simply opens a file and calls receive message. Every message until the EOF
    #      message should be written to the file just opened. When it reches the EOF
    #      message, continue execution.
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
