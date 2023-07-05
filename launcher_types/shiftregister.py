import shift_register_mgmt

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
    
    def run_step(self, step):
        """
        Runs a step in a sequence
        """
        
        self.obj.set_output_sequence({'Step': step})
