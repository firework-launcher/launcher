from serial import Serial
import socket
import time

class LauncherIOMGMT:
    def __init__(self, logging):
        self.logging = logging
        self.launchers = {}
        self.launcher_serial_ports = {}
        self.launcher_serialip = {}
    def add_launcher_serial(self, launcher_name, launcher_serial_port):
        self.launcher_serial_ports[launcher_name] = launcher_serial_port
        self.launcher_serialip[launcher_serial_port] = 'serial'
        self.launchers[launcher_name] = Serial(launcher_serial_port, 115200)
        self.logging.debug('Added launcher {} ({})'.format(launcher_name, launcher_serial_port))
    def add_launcher_ip(self, launcher_name, launcher_ip):
        self.launcher_serial_ports[launcher_name] = launcher_ip
        self.launchers[launcher_name] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.launchers[launcher_name].connect((launcher_ip, 2364))
        self.launcher_serialip[launcher_ip] = 'ip'
        self.logging.debug('Added launcher {} ({})'.format(launcher_name, launcher_ip))
    def get_launcher(self, launcher_name):
        serial_port = self.launcher_serial_ports[launcher_name]
        serial_obj = self.launchers[launcher_name]
        return serial_port, serial_obj
    def get_launcher_by_port(self, serial_port):
        new_launcher = None
        for launcher in self.launcher_serial_ports:
            if self.launcher_serial_ports[launcher] == serial_port:
                new_launcher = launcher
        return self.get_launcher(new_launcher)
    def write_to_launcher_serial(self, launcher_port, msg):
        serial_port, serial_obj = self.get_launcher_by_port(launcher_port)
        serial_obj.write(msg.encode())
        self.logging.debug('Sent serial message: {} to launcher {}'.format(msg.replace('\r\n', ''), serial_port))

        data = serial_obj.read()
        time.sleep(0.5)
        data_left = serial_obj.inWaiting()
        data += serial_obj.read(data_left)
        data = data.decode('utf-8')
        self.logging.debug('Recieved serial response: {}'.format(data.replace('\r\n', '')))
        time.sleep(0.5)
    def write_to_launcher_ip(self, launcher_ip, msg):
        launcher_ip, launcher_s = self.get_launcher_by_port(launcher_ip)
        launcher_s.send(msg.encode())
        self.logging.debug('Sent message: {} to launcher {}'.format(msg.replace('\r\n', ''), launcher_ip))

        data = launcher_s.recv(1024)
        data = data.decode('utf-8')
        self.logging.debug('Recieved response: {}'.format(data.replace('\r\n', '')))
        time.sleep(1)
    def write_to_launcher(self, launcher_port, msg):
        if self.launcher_serialip[launcher_port] == 'serial':
            self.write_to_launcher_serial(launcher_port, msg)
        else:
            self.write_to_launcher_ip(launcher_port, msg)
