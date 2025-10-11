import os
import yaml

class EntryPointSettings:
    def __init__(self, options):
        self.options = options

class PropagationSettings:
    def __init__(self, options):
        self.options = options

class SourceSettings:
    def __init__(self, options):
        self.options = options

class SinkSettings:
    def __init__(self, options):
        self.options = options

class SettingsManager:
    def __init__(self, options):
        self.options = options

        self.default_settings_dir = self.options.default_settings
        self.additional_settings_dir = self.options.additional_settings

        self.lang_to_entry_point_settings = {}
        self.lang_to_propagation_settings = {}
        self.lang_to_source_settings = {}
        self.lang_to_sink_settings = {}

    def init(self):
        print("...........", self.default_settings_dir, self.additional_settings_dir)
        #从self.default_settings_dir文件夹中扫描entry-point.yaml、propagation.yaml、source.yaml、sink.yaml文件
        for dirpath, dirnames, filenames in os.walk(self.default_settings_dir):
            for filename in filenames:
                print("haha", filename)
                file_path = os.path.join(dirpath, filename)
                file_name, file_ext = os.path.splitext(filename)
                if file_ext == ".yaml":
                    with open(file_path, "r") as f:
                        yaml_data = yaml.safe_load(f)