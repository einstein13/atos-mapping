from base64 import b64encode

from filesystem import FileSystem
from mapping_search import MappingSearch

class Core(FileSystem, MappingSearch):

    settings = {}

    def __init__(self):
        super(Core, self).__init__()
        self.settings = {}

        self.init_project()
        self.fill_mandatory_fields()
        self.full_run()
        self.finish_sequence()
        return

    def init_project(self):
        self.create_mappings_folder()
        self.create_settings_file()
        self.read_settings()
        print("Initial sequence completed\n* * * * * *\n")
        return

    def hash_password(self, username, password):
        string = username + ":" + password
        try:
            # python 3
            hashed = b64encode(bytes(string, "UTF-8")).decode("UTF-8")
        except:
            # python 2
            hashed = b64encode(string)
        return hashed
        
    def set_user(self):
        user = input('Enter username: ')
        password = input('Enter password: ')
        if user == '' or password == '':
            return ''
        return self.hash_password(user, password)

    def domain_input_query(self):
        domain = input('Enter subdomain [default: atosglobaldev]: ')
        if not domain:
            domain = 'atosglobaldev'
        return domain

    def set_domain(self):
        domain = ''
        while domain == '':
            domain = self.domain_input_query()
            if 'serivce-now.com' in domain:
                print("please type subdomain of full service-now domain name")
                domain = ''
        full_domain = "https://" + domain + ".service-now.com"
        return full_domain

    def read_settings(self):
        settings = self.read_settings_file()
        if settings:
            self.settings = settings
        return 

    def update_settings(self, dict_to_update):
        for key in dict_to_update.keys():
            self.settings[key] = dict_to_update[key]
        self.set_settings_file(self.settings)
        return

    def check_mandatory_settings(self):
        keys_to_check = [
            'credentials',
            'domain'
            ]

        settings_keys = list(self.settings.keys())
        for key in keys_to_check:
            if key not in settings_keys:
                return False
        return True

    def run_mapping_sequence(self):
        mapping_name = input('Enter mapping name: ')
        first_block_content = self.one_block_search(mapping_name)
        if first_block_content == -1:
            return
        mapping_content = self.find_full_xml(first_block_content)
        self.write_mapping_file(first_block_content['u_name'], mapping_content)
        return

    def print_help_message(self):
        text = """This program accepts commands:
    * exit - terminates the program
    * mapping - make mapping tree for everything
    * configure - change settings for password/url
Aliases are configured in lines ~110 in core.py"""
        print(text)
        return

    def input_command(self):
        command = input('Input command: ')
        command = command.lower().strip()

        if command in ['quit', 'end', 'exit', 'q']:
            return False
        elif command in ['mapping', 'map']:
            self.run_mapping_sequence()
            return True
        elif command in ['man', 'help']:
            self.print_help_message()
            return True
        elif command in ['pass', 'password', 'credentials', 'user',
                'update settings', 'update_settings', 'settings', 'domain',
                'configure']:
            self.set_connection_settings()
            return True
        print("Unknown command, try 'help'.")
        return True

    def set_connection_settings(self):
        credentials = self.set_user()
        domain = self.set_domain()
        update = {}
        update['domain'] = domain
        update['credentials'] = credentials
        self.update_settings(update)
        self.test_connection()
        return

    def fill_mandatory_fields(self):
        if not self.check_mandatory_settings():
            self.set_connection_settings()
        else:
            self.test_connection()
        return

    def finish_sequence(self):
        print("\n* * * * * *\nProgram finished\n* * * * * *")
        return

    def full_run(self):
        work_flag = True
        while work_flag:
            work_flag = self.input_command()