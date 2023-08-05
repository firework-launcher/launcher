from serial import Serial
import launcher_mgmt
import time

launcher_type = 'serial'
type_pretty_name = 'Serial'

class Launcher:
    def __init__(self, launcher_io, name, port, count):
        """
        Called in the add_launcher route on the main file. It defines some things
        about the launcher, and tells the LauncherIOMGMT object to add itself to
        the list.
        """

        self.launcher_io = launcher_io

        try:
            self.obj = Serial(port, 115200)
        except:
            raise launcher_mgmt.LauncherNotFound()
        self.name = name
        self.port = port
        self.type = 'serial'
        self.count = count
        self.armed = False
        self.sequences_supported = True

        self.launcher_io.add_launcher(self)
    
    def write_to_launcher(self, firework, state):
        """
        Writes to the launcher
        """
        
        print('Write called')
        if self.armed:
            msg = '/digital/{}/{}'.format(firework, state)

            self.obj.write(msg.encode())
            self.launcher_io.logging.debug('Sent serial message: {} to launcher {}'.format(msg.replace('\r\n', ''), self.port))

            data = self.obj.read()
            time.sleep(0.5)
            data_left = self.obj.inWaiting()
            data += self.obj.read(data_left)
            data = data.decode('utf-8')
            self.launcher_io.logging.debug('Recieved serial response: {}'.format(data.replace('\r\n', '')))
            time.sleep(0.5)
    
    def write_to_launcher_sequence(self, msg):
        """
        Writes to the launcher with no delay and not logging the response.
        """

        if self.armed:
            self.obj.write(msg.encode())
            self.launcher_io.logging.debug('Sent serial message: {} to launcher {}'.format(msg.replace('\r\n', ''), self.port))

            self.obj.read()
            data_left = self.obj.inWaiting()
            self.obj.read(data_left)
    
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
    
    def arm(self):
        self.armed = True
    
    def disarm(self):
        self.armed = False

    def remove(self):
        self.obj.close()
