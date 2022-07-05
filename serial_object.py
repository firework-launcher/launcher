from serial import Serial as Ser
import time

class Serial:
    def __init__(self, filename=None, bitrate=None, dummy_obj=False):
        self.dummy_obj = dummy_obj
        self.filename = filename
        if self.dummy_obj:
            self.ser = None
        else:
            self.ser = Ser(filename, bitrate)

    def command(self, cmd):
        if self.dummy_obj:
            return 'This is a dummy response from this command: {}'.format(cmd)
        else:
            print('Sending info, Command: {}, Serial Device: {}'.format(cmd, filename))
            ser.write(cmd.encode())
            data = ser.read()
            time.sleep(0.5)
            data_left = ser.inWaiting()
            data += ser.read(data_left)
            return data

    def close(self):
        if not self.dummy_obj:
            self.ser.close()
