import os
import time

CLK_PIN = 84
OE_PIN = 86
SER_PIN = 85
CLR_PIN = 97
RCLK_PIN = 96

class ShiftRegisterMGMT:
    def __init__(self, chip, shift_size):
        self.shift_size = shift_size
        self.chip = chip
        self.write_to_gpio([[OE_PIN, 1]])
        self.write_to_gpio([[CLR_PIN, 1]])

    def write_to_gpio(self, list_of_values):
        cmd = 'gpioset {} '.format(self.chip)
        final_command = ''
        x = 0
        for value in list_of_values:
            if x == len(list_of_values)-1:
                final_command += cmd + '{}={}'.format(value[0], value[1])
            else:
                final_command += cmd + '{}={} && '.format(value[0], value[1])
            x += 1
        os.system(final_command)

    def load_shift(self, shift):
        ser_status = None
        write_operations = []
        for seg in shift:
            if not seg == ser_status:
                write_operations.append([SER_PIN, seg])
                ser_status = seg
            write_operations.append([CLK_PIN, 1])
            write_operations.append([CLK_PIN, 0])
        write_operations.append([RCLK_PIN, 1])
        write_operations.append([RCLK_PIN, 0])
        write_operations.append([OE_PIN, 0])
        self.write_to_gpio(write_operations)
        time.sleep(1)
        self.write_to_gpio([[OE_PIN, 1]])

    def load_shift_pattern(self, shifts, delays, set_oe):
        current_delay = 0
        for shift in shifts:
            ser_status = None
            write_operations = []
            for seg in shift:
                if not seg == ser_status:
                    write_operations.append([SER_PIN, seg])
                    ser_status = seg
                write_operations.append([CLK_PIN, 1])
                write_operations.append([CLK_PIN, 0])
            write_operations.append([RCLK_PIN, 1])
            write_operations.append([RCLK_PIN, 0])
            write_operations.append([OE_PIN, 0])
            self.write_to_gpio(write_operations)
            time.sleep(delays[current_delay])
            current_delay += 1
        if set_oe:
            self.write_to_gpio([[OE_PIN, 1]])

    def set_output_pattern(self, pattern, set_oe=True):
        shifts = []
        delays = []
        for stage in pattern:
            pins = pattern[stage]['pins']
            current_shift_split = []
            for x in range(self.shift_size):
                current_shift_split.append('0')
            for pin in pins:
                current_shift_split[(self.shift_size-1)-(pin-1)] = '1'
                current_shift = ''.join(current_shift_split)
            shifts.append(current_shift)
            delays.append(pattern[stage]['delay'])
        self.load_shift_pattern(shifts, delays, set_oe)
        self.clear()

    def set_output(self, pins):
        current_shift_split = []
        for x in range(self.shift_size):
            current_shift_split.append('0')
        for pin in pins:
            current_shift_split[(self.shift_size-1)-(pin-1)] = '1'
            current_shift = ''.join(current_shift_split)
        self.load_shift(current_shift)
        self.clear()
    
    def clear(self):
        self.write_to_gpio([[CLR_PIN, 0], [CLR_PIN, 1]])