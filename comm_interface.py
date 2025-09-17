from abc import ABC, abstractmethod


class CommInterface(ABC):
    @abstractmethod
    def __init__(self, host, port):
        """Initialize the file transfer instance."""
        pass

    @abstractmethod
    def initialize_as_server(self, host, port):
        """Initialize the instance as a server."""
        pass

    @abstractmethod
    def initialize_as_client(self):
        """Initialize the instance as a client."""
        pass

    @abstractmethod
    def send_message(self, data, param="", addr=None):
        """Send a message to the specified destination address."""
        pass

    @abstractmethod
    def send_file(self, filepath, addr):
        """Read a local filepath and send the data to the specified destination address."""
        pass

    @abstractmethod
    def receive_message(self):
        """Receive a message and return data, parameters and address."""
        pass

    @abstractmethod
    def receive_file(self, filepath):
        """Receive a file and save it to the specified path."""
        pass


class CommInterfaceFactory:
    @staticmethod
    def create(comm_interface, is_server=False, host=None, port=None):
        comm_obj = comm_interface()
        if is_server:
            comm_obj.initialize_as_server(host, port)
        else:
            comm_obj.initialize_as_client()
        return comm_obj
