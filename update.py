import os
import sys
import tarfile
import time
import subprocess
import sys
import shutil

dir_list = os.listdir()
update_file = sys.argv[1]
main_pid = int(sys.argv[2])

os.kill(main_pid)

for file in dir_list:
    if not file == 'config' and not file == 'auth.sqlite' and not file == update_file:
        if os.path.isdir(file):
            shutil.rmtree(file)
        else:
            os.remove(file)

update_file_archive = tarfile.open(update_file)
update_file_archive.extractall('.')
update_file_archive.close()

os.remove(update_file)

subprocess.Popen([sys.executable, 'main.py'])
os._exit(0)
