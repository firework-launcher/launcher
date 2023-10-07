import socket
import time
import launcher_mgmt
import threading
import json
import requests

launcher_type = 'espnode'
type_pretty_name = 'ESP Node'

mappings = [4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9, 16, 15, 14, 13]

class Launcher:
    def __init__(self, launcher_io, name, ip, count):
        """
        Called in the /add_launcher path on the main file. It defines some things
        about the launcher, and tells the LauncherIOMGMT object to add itself to
        the list.
        """
        
        self.launcher_io = launcher_io

        self.send_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self.port = ip
        self.type = 'espnode'
        self.channels_connected = []
        self.armed = False
        self.count = count
        self.sequences_supported = True
        try:
            self.send_obj.connect((ip, 3333))
            self.recv_obj.connect((ip, 4444))
        except:
            raise launcher_mgmt.LauncherNotFound()
        self.cc_thread_running = True
        threading.Thread(target=self.channels_connected_thread).start()
        self.launcher_io.add_launcher(self)
    
    def find_pwm(self, channel):
        profiles = self.launcher_io.config.config['firework_profiles'][self.port]
        for profile in profiles:
            if channel in profiles[profile]['fireworks']:
                return profiles[profile]['pwm']

    def channels_connected_thread(self):
        while self.cc_thread_running:
            data_full = self.recv_obj.recv(1024).decode('utf-8').split('\r\n')
            for data in data_full:
                try:
                    data = json.loads(data)
                except json.decoder.JSONDecodeError:
                    pass
                else:
                    inputs = data['inputData']
                    if not inputs == []:
                        data1 = '{0:b}'.format(inputs[0])
                        zeros_to_add = 8-len(data1)
                        zero_string = ''
                        for zero in range(zeros_to_add):
                            zero_string += '0'
                        data1 = zero_string + data1

                        data2 = '{0:b}'.format(inputs[1])
                        zeros_to_add = 8-len(data2)
                        zero_string = ''
                        for zero in range(zeros_to_add):
                            zero_string += '0'
                        data2 = zero_string + data2

                        data = data1 + data2
                        new_data = list('0000000000000000')
                        x = 0
                        for mapping in mappings:
                            mapping -= 1
                            new_data[mapping] = data[x]
                            x += 1
                        data = ''.join(new_data)
                        x = 1
                        channels_connected_new = []
                        for bit in data:
                            if bit == '1':
                                channels_connected_new.append(x)
                            x += 1
                        if not channels_connected_new == self.channels_connected:
                            self.channels_connected = channels_connected_new
                            try:
                                requests.get('http://localhost/update_connected_channels')
                            except:
                                pass
        self.recv_obj.close()
    
    def write_to_launcher(self, firework, state):
        """
        Writes to the launcher
        """

        firework -= 1

        if self.armed:
            if state == 1:
                self.send_obj.send(json.dumps({
                    'code': 1,
                    'payload': [firework, self.find_pwm(firework)]
                }).encode())
                self.launcher_io.logging.debug('Triggered firework {} on launcher {}'.format(firework, self.port))
            time.sleep(1)
    
    def run_step(self, step):
        """
        Creates a dictionary to send to the ESP that has the correct format
        """

        if self.armed:
            pin_pwm = []
            for pin in step['pins']:
                pin_pwm.append(self.find_pwm(pin))

            data = {'code': 4, 'payload': [step['pins'], pin_pwm]}
            self.send_obj.send(json.dumps(data).encode())
            self.launcher_io.logging.debug('Sent step to ESP Node: {} ({})'.format(self.name, self.port))
            time.sleep(1)
            time.sleep(int(step['delay']))

    def arm(self):
        self.send_obj.send(json.dumps({
                    'code': 2,
                }).encode())
        self.armed = True
    
    def disarm(self):
        self.send_obj.send(json.dumps({
                    'code': 3,
                }).encode())
        self.armed = False

    def remove(self):
        self.send_obj.close()
        self.cc_thread_running = False
