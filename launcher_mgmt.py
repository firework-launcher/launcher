from serial import Serial
import socket
import time
import shift_register_mgmt

class LauncherNotFound(Exception):
    pass

class LauncherIOMGMT:
    def __init__(self, logging):
        self.logging = logging
        self.launchers = {}

    def add_launcher(self, launcher):
        """
        Code ran by the seperate launcher classes below on init.
        It just logs that whatever launcher was added and adds it to the list.
        It stores the launcher in the dictionary self.launchers by setting the
        key to the launcher port (or id), and setting the value to the object.
        """

        self.launchers[launcher.port] = launcher
        self.logging.debug('Added launcher {} ({})'.format(launcher.name, launcher.port))

    def write_to_launcher(self, launcher_port, msg, firework):
        """
        Code ran by the queue thread to launch a firework. This just makes sure
        the firework number does not exceed the amount of fireworks in the 
        launcher, and runs the function in the launcher object for writing to it.
        """

        if firework <= self.launchers[launcher_port].count:
            self.launchers[launcher_port].write_to_launcher(msg)

    def get_ports(self):
        """
        This is used to just get a list of all the launchers with the name being
        the key, and the value being the port.
        """

        port_list = {}
        for launcher in self.launchers:
            port_list[self.launchers[launcher].name] = launcher
        return port_list


class SerialLauncher:
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
            raise LauncherNotFound()
        self.name = name
        self.port = port
        self.type = 'serial'
        self.count = count

        self.launcher_io.add_launcher(self)
    
    def write_to_launcher(self, msg):
        """
        Writes to the launcher
        """

        self.obj.write(msg.encode())
        self.launcher_io.logging.debug('Sent serial message: {} to launcher {}'.format(msg.replace('\r\n', ''), self.port))

        data = self.obj.read()
        time.sleep(0.5)
        data_left = self.obj.inWaiting()
        data += self.obj.read(data_left)
        data = data.decode('utf-8')
        self.launcher_io.logging.debug('Recieved serial response: {}'.format(data.replace('\r\n', '')))
        time.sleep(0.5)


class ShiftRegisterLauncher:
    def __init__(self, launcher_io, name, chip, count):
        """
        Called in the add_launcher route on the main file. It defines some things
        about the launcher, and tells the LauncherIOMGMT object to add itself to
        the list.
        """

        self.launcher_io = launcher_io

        try:
            self.obj = shift_register_mgmt.ShiftRegisterMGMT(chip, count)
        except:
            raise LauncherNotFound()
        self.name = name
        self.port = chip
        self.type = 'shiftregister'
        self.count = count

        self.launcher_io.add_launcher(self)
    
    def write_to_launcher(self, msg):
        """
        Writes to the launcher
        """

        msg = msg.split('/')
        pin = int(msg[2])-1
        value = int(msg[3])
        if value == 1:
            self.obj.set_output([pin])
            self.launcher_io.logging.debug('Triggered firework {} on shift register {}'.format(pin, self.port))


class IPLauncher:
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
            raise LauncherNotFound()
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
