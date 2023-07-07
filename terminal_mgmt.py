import subprocess

class Terminals:
    def __init__(self):
        self.open_terminal_processes = {}
    def create_terminal(self, port, small_screen):
        if small_screen:
            cols = 100
            rows = 70
        else:
            cols = 200
            rows = 50
        self.open_terminal_processes[str(port)] = subprocess.Popen(['tty-share', '-headless', '--listen', '0.0.0.0:{}'.format(port), '-headless-cols', str(cols), '-headless-rows', str(rows)])
    def delete_terminal(self, port):
        self.open_terminal_processes[port].kill()
        del self.open_terminal_processes[port]
