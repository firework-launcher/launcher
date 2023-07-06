import socket
import time
import launcher_mgmt

launcher_type = 'ip'
type_pretty_name = 'IP'

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
        self.type = 'ip'
        self.count = count
        try:
            self.obj.connect((ip, 2364))
        except:
            raise launcher_mgmt.LauncherNotFound()
        self.launcher_io.add_launcher(self)
    
    def write_to_launcher(self, msg):
        """
        Writes to the launcher
        """

        self.obj.send(msg.encode())
        self.launcher_io.logging.debug('Sent message: {} to launcher {}'.format(msg.replace('\r\n', ''), self.port))

        data = self.obj.recv(1024)
        data = data.decode('utf-8')
        self.launcher_io.logging.debug('Recieved response: {}'.format(data.replace('\r\n', '')))
        time.sleep(1)
    
    def write_to_launcher_sequence(self, msg):
        """
        Writes to the launcher with no delay and not logging the response.
        """

        self.obj.send(msg.encode())
        self.launcher_io.logging.debug('Sent message: {} to launcher {}'.format(msg.replace('\r\n', ''), self.port))

        data = self.obj.recv(1048576)
    
    def run_step(self, step):
        """
        Runs a step in a sequence
        """

        command = ''
        for pin in step['pins']:
            command += '/digital/{}/0\r\n'.format(pin)
        self.write_to_launcher_sequence(command)

        time.sleep(1)

        command = ''
        for pin in step['pins']:
            command += '/digital/{}/1\r\n'.format(pin)
        self.write_to_launcher_sequence(command)

        time.sleep(int(step['delay']))
