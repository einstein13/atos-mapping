try: # Python 3+
    from urllib.request import Request, urlopen
    # from urllib.parse import urlencode, quote
except: # Pyton 2.7
    from urllib2 import Request, urlopen
    # from urllib import urlencode, quote
from json import loads, dumps
from re import compile as comp
from xml.etree.ElementTree import Element, SubElement
from xml.etree.ElementTree import tostring, dump
try:
    # Python 3.5+
    from html import unescape
except:
    try:
        # Python 3.4-
        from html.parser import HTMLParser
    except:
        # Python 2.7
        from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape

def indent(elem, level=0, more_sibs=False):
    # based on https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    ind = "    "
    i = "\n"
    if level:
        i += (level-1) * ind
    num_kids = len(elem)
    if num_kids:
        if not elem.text or not elem.text.strip():
            elem.text = i + ind
            if level:
                elem.text += ind
        count = 0
        for kid in elem:
            indent(kid, level+1, count < num_kids - 1)
            count += 1
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
            if more_sibs:
                elem.tail += ind
    else:
        if elem.text:
            elem.text = elem.text.replace("\n", i+ind*2)
            elem.text = elem.text.replace("\r", "")
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            if more_sibs:
                elem.tail += ind
    return elem

class MappingSearch(object):

    mapping_block_table = "u_sr_mapping_block"
    mapping_line_table = "u_sr_mapping_line"

    used_mapping_blocks = []

    def connect(self, table, query=None):
        url = self.settings['domain'] + "/api/now/table/" + table
        if query:
            url += "?" + query

        headers = {}
        headers['Authorization'] = "Basic " + self.settings['credentials']
        headers['Accept'] = "application/json"
        headers['Content-Type'] = "application/json"

        request_object = Request(url, headers=headers)
        try:
            connection = urlopen(request_object)
        except Exception as e:
            print("Connection error:")
            print(e)
            return False
        result = connection.read().decode("UTF-8")

        try:
            result = loads(result)
        except:
            print("Error occured while parsing the output:")
            print(result)
            return False

        return result

    def test_connection(self):
        query = "sysparm_limit=1"
        print("Testing connection...")
        result = self.connect(self.mapping_block_table, query)
        if result:
            print("Connection OK.")
        else:
            print("Testing connection failed. Please retry.")
        return

    def add_key_value_to_xml(self, xml, key, value=False):
        subelement = SubElement(xml, key)
        if value:
            subelement.text = value
        return subelement

    def find_mapping_lines(self, block_data):
        query = "sysparm_query=u_mapping_block%%3D%s%%5Eu_active%%3Dtrue%%5EORDERBYu_order" % (block_data['sys_id'], )
        result = self.connect(self.mapping_line_table, query)
        if not result:
            return False
        lines = result['result']
        return lines

    def find_mapping_block(self, block_name):
        print("Retrieving info about block: " + block_name)
        query = "sysparm_query=u_name%3D" + block_name
        result = self.connect(self.mapping_block_table, query)
        if not result:
            print("ERR (Retrieving block): wrong response")
            return False
        if not 'result' in list(result.keys()):
            print("ERR (Retrieving block): no result")
            return False
        if len(result['result']) == 0:
            print("ERR (Retrieving block): no block data")
            return False
        block = result['result'][0]
        return block

    def mapping_block_names_search(self, script):
        pattern = "\s*return [\"'](.*)[\"'];"
        regex = comp(pattern)
        results = []
        for line in script.split("\n"):
            match = regex.match(line)
            if match:
                results.append(match.group(1))
        return results

    def add_mapping_lines_to_xml(self, xml, line_data):
        valid_keys = [["u_output_parm", "TargetParam"], ["u_type", "Type"],
                ["u_order", "Order"], ["u_value", "Value"],
                ["u_script", "Script"], ["u_comment", "Comment"]]
        line_keys = list(line_data.keys())
        for key in valid_keys:
            if key[0] in line_keys and line_data[key[0]]:
                self.add_key_value_to_xml(xml, key[1], line_data[key[0]])
        if line_data['u_type'] == 'includeMap':
            if 'u_value' in line_keys and line_data['u_value']:
                included = SubElement(xml, "MappingBlock")
                mapping_block_data = self.find_mapping_block(line_data['u_value'])
                if mapping_block_data is not False:
                    self.add_mapping_block_to_xml(included, mapping_block_data)
            if 'u_script' in line_keys and line_data['u_script']:
                blocks = self.mapping_block_names_search(line_data['u_script'])
                for name in blocks:
                    included = SubElement(xml, "MappingBlock")
                    mapping_block_data = self.find_mapping_block(name)
                    if mapping_block_data is not False:
                        self.add_mapping_block_to_xml(included, mapping_block_data)
        if line_data['u_type'] == 'nextMap':
            if 'u_value' in line_keys and line_data['u_value']:
                return [line_data['u_value']]
            if 'u_script' in line_keys and line_data['u_script']:
                blocks = self.mapping_block_names_search(line_data['u_script'])
                return blocks
        return []

    def add_lines_to_block_xml(self, xml, block_data):
        lines = self.find_mapping_lines(block_data)
        if not lines or len(lines) == 0:
            return False
        for line_data in lines:
            line_xml = SubElement(xml, "Line")
            next_maps = self.add_mapping_lines_to_xml(line_xml, line_data)
            if len(next_maps) > 0:
                return next_maps
        return []

    def add_mapping_block_to_xml(self, xml, block_data):
        valid_keys = [['u_name', 'Name'], ['u_phase', 'Phase'],
            ['u_output_ps', 'TargetParamSet'] , ['u_selector', 'Selector']]
        block_keys = list(block_data.keys())
        for key in valid_keys:
            if key[0] in block_keys and block_data[key[0]]:
                self.add_key_value_to_xml(xml, key[1], block_data[key[0]])
        lines = self.add_key_value_to_xml(xml, 'MappingLines')
        next_maps = self.add_lines_to_block_xml(lines, block_data)
        if 'u_name' in block_keys and block_data['u_name']:
            self.used_mapping_blocks.append(block_data['u_name'])
        self.used_mapping_blocks

        return next_maps

    def check_mapping_blocks_duplicates(self):
        used_blocks = self.used_mapping_blocks
        if len(set(used_blocks)) == len(used_blocks):
            return
        for block_name in set(used_blocks):
            if used_blocks.count(block_name) > 1:
                print("WARNING: duplicate include of \"%s\"" % (block_name,))
        return

    def find_full_xml(self, block_data):
        self.used_mapping_blocks = []
        basic_mapping = Element("mapping")
        
        mapping_block_data = [block_data]
        while len(mapping_block_data) > 0:
            block_xml = SubElement(basic_mapping, "MappingBlock")
            next_maps = self.add_mapping_block_to_xml(block_xml, mapping_block_data[0])
            mapping_block_data.pop(0)
            for one_map in next_maps:
                mapping_block_data.append(self.find_mapping_block(one_map))

        self.check_mapping_blocks_duplicates()

        indent(basic_mapping)
        string = tostring(basic_mapping).decode("UTF-8")
        string = unescape(string)
        return string

    def one_block_search(self, block_name):
        query = "sysparm_query=u_nameLIKE" + block_name
        query += "%5EORDERBYu_output_ps"
        query += "&sysparm_limit=30"
        result = self.connect(self.mapping_block_table, query)
        if not result:
            return -1
        
        lines = result['result']
        if len(lines) == 1:
            return lines[0]

        print("\nFound more matching results (pick one-number):")
        itr = 0
        itr_max = len(lines)
        while itr < itr_max:
            print("%d: %s (%s)" %(itr, lines[itr]['u_name'], lines[itr]['u_output_ps']))
            itr += 1

        input_number = -2
        while input_number < 0:
            input_number = input("Select proper name (-1 for other search): ")
            try:
                input_number = int(input_number)
            except:
                input_number = -2
            if input_number == -1:
                return -1
            if input_number > len(lines)-1:
                input_number = -2
        return lines[input_number]

