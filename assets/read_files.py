import json

class read_file:
    def read_json_file(self, file_name):
        with open(f'./config/{file_name}.json', 'r', encoding='utf-8') as response:
            return json.load(response)