import os
import time

CLK_PIN = 84
OE_PIN = 86
SER_PIN = 85
CLR_PIN = 97
RCLK_PIN = 96

class ShiftRegisterMGMT:
    def __init__(self, chip, shift_size):
        """
        Sets pins that need to be set.
        """

        self.shift_size = shift_size
        self.chip = chip
        if not os.path.exists(self.chip):
            raise FileNotFoundError()
        self.clear()
        self.write_to_gpio([[OE_PIN, 1], [SER_PIN, 0], [CLK_PIN, 0], [RCLK_PIN, 0]])

    def write_to_gpio(self, list_of_values):
        """
        Sets pins to high or low. It accepts multiple operations
        since gpioset can handle it. This way it is faster since
        gpioset is written in C and I won't have to run a seperate
        command each time.
        """

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
        """
        Send binary value to shift register.
        """
        
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
        """
        Similar to load shift, this accepts multiple shifts and
        delays to make a pattern. The set_oe parameter is there
        for if the pattern is supposed to loop. I think it will
        mostly be True, meaning that it will not loop. The only
        reason this would be False is if I would make a pattern
        for just the LEDs on the board.
        """

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
            time.sleep(1)
            self.write_to_gpio([[OE_PIN, 1]])
            time.sleep(int(delays[current_delay]))
            current_delay += 1
        if set_oe:
            self.write_to_gpio([[OE_PIN, 1]])

    def set_output_pattern(self, pattern, set_oe=True):
        """
        Accepts a dictionary containing steps for a pattern
        with the fireworks that need to be launched, and the
        delays. The set_oe parameter is explained in the
        load_shift_pattern() function.
        """

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
        threading.Thread(target=self.load_shift_pattern(shifts, delays, set_oe)).start()
        self.clear()

    def set_output(self, pins):
        """
        Given a list of fireworks to launch, and runs the
        load_shift() function for them.
        """

        current_shift_split = []
        for x in range(self.shift_size):
            current_shift_split.append('0')
        for pin in pins:
            current_shift_split[(self.shift_size-1)-(pin-1)] = '1'
        current_shift = ''.join(current_shift_split)
        self.load_shift(current_shift)
        self.clear()
    
    def clear(self):
        """
        Clears the shift register.
        """

        self.write_to_gpio([[CLR_PIN, 0], [CLR_PIN, 1]])
