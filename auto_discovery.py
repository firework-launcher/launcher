import socket
import time
import requests

class AutoDiscovery:
    def __init__(self, launcher_io, config):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setblocking(0)
        self.launcher_io = launcher_io
        self.config = config
    
    def add_launcher(self, node):
        requests.post('http://localhost/add_node_discover', data={'node': node})

    def discover(self):
        while True:
            self.socket.sendto(b'NODE_DISCOVERY', ('255.255.255.255', 3344))
            start_time = time.time()
            while time.time() - start_time < 5:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    if data.decode() == "NODE_RESPONSE":
                        self.add_launcher(addr[0])
                except socket.error:
                    pass
