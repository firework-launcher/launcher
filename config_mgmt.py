import os
import json

class ConfigMGMT:
    def __init__(self):
        self.config_dir = 'config/'
        self.config = {}
        self.config_metadata = {}

        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)

    def load_file(self, file, placeholder_data={}):
        """
        Create config file if it does not exist,
        load the data into self.config if it does,
        Put the full filename in self.config_metadata
        So save_config() can know where to save.
        """

        if not os.path.exists(self.config_dir + file):
            f = open(self.config_dir + file, 'x')
            f.write(json.dumps(placeholder_data, indent=4))
            f.close()
        f = open(self.config_dir + file)
        data = json.loads(f.read())
        f.close()
        filename_no_ext = file.split('.')[0]
        self.config[filename_no_ext] = data
        self.config_metadata[filename_no_ext] = {'filename': file}

    def save_config(self):
        """
        Save all config files
        """

        for file in self.config:
            f = open(self.config_dir + self.config_metadata[file]['filename'], 'w')
            f.write(json.dumps(self.config[file], indent=4))
            f.close()
