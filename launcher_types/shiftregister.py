import shift_register_mgmt
import launcher_mgmt

launcher_type = 'shiftregister'
type_pretty_name = 'Shift Register'

class Launcher:
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
            raise launcher_mgmt.LauncherNotFound()
        self.name = name
        self.port = chip
        self.type = 'shiftregister'
        self.count = count
        self.sequences_supported = True
        self.channels_connected = None
        self.armed = False

        self.launcher_io.add_launcher(self)
    
    def write_to_launcher(self, pin, value):
        """
        Writes to the launcher
        """
        if self.armed:
            pin -= -1
            if value == 1:
                self.obj.set_output([pin])
                self.launcher_io.logging.debug('Triggered firework {} on shift register {}'.format(pin, self.port))
    
    def run_step(self, step):
        """
        Runs a step in a sequence
        """
        
        self.obj.set_output_sequence({'Step': step})
    
    def arm(self):
        self.armed = True
    
    def disarm(self):
        self.armed = False

    def remove(self):
        pass
