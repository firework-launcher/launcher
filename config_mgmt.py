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
            file_obj = open(self.config_dir + file, 'x')
            file_obj.write(json.dumps(placeholder_data, indent=4))
            file_obj.close()
        file_obj = open(self.config_dir + file)
        data = json.loads(file_obj.read())
        file_obj.close()
        filename_no_ext = file.split('.')[0]
        self.config[filename_no_ext] = data
        self.config_metadata[filename_no_ext] = {'filename': file}

    def save_config(self):
        """
        Save all config files
        """

        for file in self.config:
            file_obj = open(self.config_dir + self.config_metadata[file]['filename'], 'w')
            file_obj.write(json.dumps(self.config[file], indent=4))
            file_obj.close()
