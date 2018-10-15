
from os import path, pardir, makedirs, rename
from json import loads, dump

class FileSystem():

    settings_file = 'settings.json'
    mapppings_folder = 'mappings'

    def get_project_path(self):
        basic_folder_names = ["atos-mapping", "atos-mapping-master"]
        file_path = path.abspath(__file__)
        folder_path = file_path
        while True:
            splitted = folder_path.split("\\") # Windows
            if len(splitted) == 1:
                splitted = folder_path.split("/") # Linux
            # now "splitted" is a path splitted into folders
            if splitted[-1] in basic_folder_names:
                # found correct path
                break
            # save old path
            old_path = folder_path
            # create new path - less by one folder
            folder_path = path.abspath(path.join(folder_path, pardir))
            if old_path == folder_path:
                # if that is the end of the path
                self.output_queue.append({'type': 'text', 'message': 'There was a problem with recognizing the path'})
                return None
        return folder_path

    def get_parent_project_path(self):
        project_path = self.get_project_path()
        if project_path is None:
            return None
        folder_path = path.abspath(path.join(project_path, pardir))
        return folder_path

    def create_mappings_folder(self):
        parent = self.get_parent_project_path()
        mapping_path = path.join(parent, self.mapppings_folder)
        if path.isdir(mapping_path):
            return
        makedirs(mapping_path)
        return

    def find_settings_file_path(self):
        project = self.get_project_path()
        settings_file = path.join(project, self.settings_file)
        return settings_file

    def create_settings_file(self):
        settings_file = self.find_settings_file_path()
        if path.isfile(settings_file):
            return
        file = open(settings_file, "w")
        file.write("{}")
        file.close()
        return

    def read_settings_file(self):
        settings_file = self.find_settings_file_path()
        file = open(settings_file, "r")
        content = file.read()
        file.close()
        try:
            return loads(content)
        except:
            pass
        return {}

    def set_settings_file(self, dictionary):
        settings_file = self.find_settings_file_path()
        file = open(settings_file, "w")
        # json = loads(dictionary)
        dump(dictionary, file)
        file.close()
        return

    def write_mapping_file(self, file_name, file_content):
        file_path = self.get_parent_project_path()
        file_path = path.join(file_path, self.mapppings_folder)
        file_path = path.join(file_path, file_name + ".xml")
        file = open(file_path, "w")
        file.write(file_content)
        file.close()
        return