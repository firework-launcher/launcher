import socket
import time
import launcher_mgmt
import json

launcher_type = 'espnode'
type_pretty_name = 'ESP Node'

class Launcher:
    def __init__(self, launcher_io, name, ip, count):
        """
        Called in the /add_launcher path on the main file. It defines some things
        about the launcher, and tells the LauncherIOMGMT object to add itself to
        the list.
        """
        
        self.launcher_io = launcher_io

        self.obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self.port = ip
        self.type = 'espnode'
        self.count = count
        self.sequences_supported = False
        try:
            self.obj.connect((ip, 3333))
        except:
            raise launcher_mgmt.LauncherNotFound()
        self.launcher_io.add_launcher(self)
    
    def write_to_launcher(self, firework, state):
        """
        Writes to the launcher
        """

        if state == 1:
            self.obj.send(json.dumps({
                'code': 1,
                'payload': [firework-1]
            }).encode())
            self.launcher_io.logging.debug('Triggered firework {} on launcher {}'.format(firework-1, self.port))
        time.sleep(0.5)
    
    def remove(self):
        self.obj.close()
