import time
import traceback
import sys
import os
import random
import threading

class LauncherNotFound(Exception):
    pass

class LauncherIOMGMT:
    def __init__(self, config, logging):
        self.logging = logging
        self.launchers = {}
        self.running_sequence_data = {}
        self.config = config
        self.load_launcher_types()

    def load_launcher_types(self):
        self.launcher_types = {}
        self.launcher_type_metadata = {}
        launcher_types = os.listdir('launcher_types')
        sys.path.insert(0, 'launcher_types')
        for launcher_type in launcher_types:
            if launcher_type.endswith('.py'):
                launcher_type_imported = __import__(launcher_type.replace('.py', ''), fromlist=[''])
                self.launcher_type_metadata[launcher_type_imported.launcher_type] = {'pretty_name': launcher_type_imported.type_pretty_name}
                self.launcher_types[launcher_type_imported.launcher_type] = launcher_type_imported.Launcher

    def add_launcher(self, launcher):
        """
        Code ran by the seperate launcher classes below on init.
        It just logs that whatever launcher was added and adds it to the list.
        It stores the launcher in the dictionary self.launchers by setting the
        key to the launcher port (or id), and setting the value to the object.
        """

        self.launchers[launcher.port] = launcher
        self.logging.debug('Added launcher {} ({})'.format(launcher.name, launcher.port))

    def trigger_firework(self, launcher_port, firework):
        """
        Code ran by the queue thread to launch a firework. This just makes sure
        the firework number does not exceed the amount of fireworks in the 
        launcher, and runs the function in the launcher object for writing to it.
        """

        if (firework-1) <= self.launchers[launcher_port].count:
            self.launchers[launcher_port].write_to_launcher(firework)

    def get_ports(self):
        """
        This is used to just get a list of all the launchers with the name being
        the key, and the value being the port.
        """

        port_list = {}
        for launcher in self.launchers:
            port_list[self.launchers[launcher].name] = launcher
        return port_list
    
    def get_launchers_in_sequence(self, sequence_data):
        """
        Takes all launchers being used in a sequence. This is used to find out
        if all launchers are armed in the sequence.
        """

        launchers = []
        for step in sequence_data:
            for launcher in sequence_data[step]['pins']:
                if not launcher in launchers:
                    launchers.append(launcher)
        return launchers

    def run_sequence(self, sequence_name, sequence_data):
        """
        This runs a sequence. The sequence data variable is a dictionary. The keys
        are the name of the step. The value is another dictionary. In this
        dictionary, it has 3 keys: pins, delay, and launcher. The pins value is
        an array, tells what pins need to go on at that step. The delay
        is an integer, tells how long in seconds to wait after the pins are
        pulsed. The launcher is the port of the launcher that it should pulse the
        pins on.
        """

        thread_id = random.randrange(1, 1000000)
        self.running_sequence_data[sequence_name] = {'stop': False, 'error': False, 'next_step_epoch_est': 0, 'runthread_id': thread_id}
        all_launchers = self.get_launchers_in_sequence(sequence_data)
        all_armed = True
        for launcher in all_launchers:
            if not self.launchers[launcher].armed:
                all_armed = False
        if not all_armed:
            self.running_sequence_data[sequence_name]['error'] = 'unarmed'
        else:
            for step in sequence_data:
                if not self.running_sequence_data[sequence_name]['runthread_id'] == thread_id:
                    break
                try:
                    if self.running_sequence_data[sequence_name]['stop']:
                        break
                    self.running_sequence_data[sequence_name]['step'] = step
                    self.running_sequence_data[sequence_name]['next_step_epoch_est'] = int(time.time())+int(sequence_data[step]['delay'])+1
                    x = len(sequence_data[step]['pins'])
                    for launcher in sequence_data[step]['pins']:
                        x -= 1
                        if x == 0:
                            break
                        threading.Thread(target=self.launchers[launcher].run_step, args=[{'pins': sequence_data[step]['pins'][launcher], 'delay': sequence_data[step]['delay']}]).start()
                    self.launchers[launcher].run_step({'pins': sequence_data[step]['pins'][launcher], 'delay': sequence_data[step]['delay']})
                except:
                    print(traceback.format_exc())
                    self.running_sequence_data[sequence_name]['error'] = 'failed'
                    self.running_sequence_data[sequence_name]['next_step_epoch_est'] = 0
                    break
