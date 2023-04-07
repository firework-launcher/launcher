from serial import Serial
import time

class SerialMGMT:
    def __init__(self, logging):
        self.logging = logging
        self.launchers = {}
        self.launcher_serial_ports = {}
    def add_launcher(self, launcher_name, launcher_serial_port):
        self.launcher_serial_ports[launcher_name] = launcher_serial_port
        self.launchers[launcher_name] = Serial(launcher_serial_port, 115200)
        self.logging.debug('Added launcher {} ({})'.format(launcher_name, launcher_serial_port))
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
    def write_to_launcher(self, launcher_port, msg):
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
