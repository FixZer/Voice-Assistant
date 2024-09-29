from microphone_recording import *
from assets.read_files import read_file
import threading
import os
import sys
import psutil
import sounddevice
import webbrowser
import copy

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QUrl, pyqtSlot, QObject, QCoreApplication
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

bridge = None

read_settings = read_file()
read_settings = read_settings.read_json_file('settings')
name_active = read_settings['address']
assistant = read_settings['assistant']
turn_off = read_settings['turn_off']
device_index = read_settings['device_index']

required_files = [ 
    'check.wav',
    'congratulation.wav',
    'error.wav',
    'hello_1.wav',
    'hello_2.wav',
    'not_information.wav',
    'off.wav',
    'ok_1.wav',
    'ok_2.wav',
    'ok_3.wav',
    'ok_4.wav',
    'reset.wav',
    'response_1.wav',
    'response_2.wav',
    'response_3.wav',
    'thanks.wav'
]

class PythonBridge(QObject):
    def __init__(self):
        super().__init__()
        self.active_assistant = False

    @pyqtSlot(result=str)
    def get_information(self):
        information = {
            'name': 'Голосовой помощник',
            'version': 'v0.5 BETA',
            'name_active': name_active,
            'author': '© 2024. Автор проекта: FixZer'
        }
        return json.dumps(information)
    
    @pyqtSlot(result=str)
    def get_active_assistant(self):

        devices = sounddevice.query_devices()

        default_input_device = sounddevice.default.device[0]

        process = psutil.Process(os.getpid())

        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)

        information = {
            'active': self.active_assistant,
            'microphone': f'{devices[default_input_device]["name"]}',
            'ram': int(memory_usage_mb),
            'name_active': name_active
        }
        return json.dumps(information)

    @pyqtSlot(result=str)
    def all_settings_assistant(self):

        audio_directory = os.path.join(os.getcwd(), 'audio')

        folders = [f.path for f in os.scandir(audio_directory) if f.is_dir()]

        folders_name = []

        for folder in folders:
            all_files_found = True

            for file_name in required_files:
                file_path = os.path.join(folder, file_name)
                if not os.path.exists(file_path):
                    all_files_found = False
                    break
            
            if all_files_found:
                folder = folder.split('\\')
                folders_name.append(folder[-1])

        information = {
            'address': name_active,
            'assistant': assistant,
            'folders': folders_name,
            'turn_off': turn_off
        }
        return json.dumps(information)

    @pyqtSlot(str)
    def all_settings_assistant_save(self, new_all_settings):
        file_settings = os.path.join(os.getcwd(), 'config/settings.json')

        if os.path.exists(file_settings):
            with open(file_settings, 'r', errors='ignore', encoding='utf-8') as old_settings:
                all_settings = json.loads(old_settings.read())

            old_all_settings = copy.deepcopy(all_settings)
            new_all_settings = json.loads(new_all_settings)

            for key, value in all_settings.items():
                try:
                    value = value.lower()
                    # print(f'{value} -> {new_all_settings[key]}')
                    # print('Сошло' if value == new_all_settings[key].lower() else 'Не подошло')
                    if value != new_all_settings[key].lower():
                        all_settings[key] = new_all_settings[key].lower()
                except: pass
            
            # print(all_settings)
            # print(old_all_settings)

            if all_settings != old_all_settings:
                # print('Настройки различаются')
                with open(file_settings, 'w', errors='ignore', encoding='utf-8') as new_settings:
                    json.dump(all_settings, new_settings, ensure_ascii=False, indent=4)
                
                restart_script()

    @pyqtSlot(result=str)
    def device_settings_assistant(self):

        microphones = []

        devices = sounddevice.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                if 'Микрофон' in device['name']:
                    try:
                        with sounddevice.InputStream(device=device['name']):
                            microphones.append((i, device['name']))
                    except: pass

        information = {
            'device_index': device_index,
            'devices': microphones
        }
        return json.dumps(information)

    @pyqtSlot(int)
    def device_settings_assistant_save(self, new_device_index):
        file_settings = os.path.join(os.getcwd(), 'config/settings.json')

        if os.path.exists(file_settings):
            with open(file_settings, 'r', errors='ignore', encoding='utf-8') as old_settings:
                all_settings = json.loads(old_settings.read())
            
            if all_settings['device_index'] != new_device_index:
                all_settings['device_index'] = new_device_index
                with open(file_settings, 'w', errors='ignore', encoding='utf-8') as new_settings:
                    json.dump(all_settings, new_settings, ensure_ascii=False, indent=4)
                
                restart_script()

    @pyqtSlot(result=str)
    def info_commands(self):
        file_commands = os.path.join(os.getcwd(), 'config/commands.json')

        if os.path.exists(file_commands):
            with open(file_commands, 'r', errors='ignore', encoding='utf-8') as file:
                commands = json.load(file)
            
            return json.dumps(commands)

    @pyqtSlot(str, result=str)
    def info_command(self, command_name):
        file_commands = os.path.join(os.getcwd(), 'config/commands.json')

        if os.path.exists(file_commands):
            with open(file_commands, 'r', errors='ignore', encoding='utf-8') as file:
                commands = json.load(file)
            
            # Получаем детали команды по имени
            command_details = commands[command_name]
            return json.dumps(command_details)

    @pyqtSlot(str)
    def delete_command(self, command_name):
        file_commands = os.path.join(os.getcwd(), 'config/commands.json')

        if os.path.exists(file_commands):
            with open(file_commands, 'r', errors='ignore', encoding='utf-8') as file:
                commands = json.load(file)
            
            if command_name in commands:
                del commands[command_name]

                with open(file_commands, 'w', errors='ignore', encoding='utf-8') as file:
                    json.dump(commands, file, ensure_ascii=False, indent=4)

    @pyqtSlot(str)
    def save_command(self, command_settings):
        file_commands = os.path.join(os.getcwd(), 'config/commands.json')

        if os.path.exists(file_commands):
            with open(file_commands, 'r', errors='ignore', encoding='utf-8') as file:
                commands = json.load(file)
            
            command_settings = json.loads(command_settings)

            name_command = command_settings['name_command']

            try:
                if commands[name_command]:
                    return
            except: pass

            command_data = {
                "word": command_settings['word'].lower(),
                "url": command_settings['url_text'],
                "program": command_settings['file_text']
            }

            commands[name_command] = command_data

            with open(file_commands, 'w', errors='ignore', encoding='utf-8') as file:
                json.dump(commands, file, ensure_ascii=False, indent=4)

    @pyqtSlot(str, str)
    def re_record_command(self, command_settings, old_name_command):
        file_commands = os.path.join(os.getcwd(), 'config/commands.json')

        if os.path.exists(file_commands):
            with open(file_commands, 'r', errors='ignore', encoding='utf-8') as file:
                commands = json.load(file)
            
            command_settings = json.loads(command_settings)

            name_command = command_settings['name_command']
            if old_name_command != name_command:
                if old_name_command in commands:
                    del commands[old_name_command]

            command_data = {
                "word": command_settings['word'].lower(),
                "url": command_settings['url_text'],
                "program": command_settings['file_text']
            }

            commands[name_command] = command_data

            with open(file_commands, 'w', errors='ignore', encoding='utf-8') as file:
                json.dump(commands, file, ensure_ascii=False, indent=4)

    @pyqtSlot(str)
    def transition(self, link):
        webbrowser.open(link)

    @pyqtSlot(bool)
    def set_active_assistant(self, active):
        self.active_assistant = active

class UI(QWidget):
    def __init__(self):
        super().__init__()

        global bridge

        icon_path = os.path.join(os.getcwd(), 'Program_Icon.ico')
        self.setWindowIcon(QIcon(icon_path))

        self.browser = QWebEngineView()
        src = os.path.join(os.getcwd(), 'assets/web/main.html')
        self.browser.setUrl(QUrl.fromLocalFile(src))  # Замените /path_to_your_file/ на реальный путь к вашему файлу

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.browser)

        self.setLayout(layout)
        self.setFixedSize(700, 700)
        #self.setGeometry(100, 100, 700, 700)  # Установите желаемые размеры окна
        self.setWindowTitle(f'Voice Assistant')
        self.show()

        # Устанавливаем QWebChannel
        self.channel = QWebChannel()
        self.bridge = PythonBridge()
        bridge = self.bridge
        self.channel.registerObject("python", self.bridge)
        self.browser.page().setWebChannel(self.channel)
    
    def closeEvent(self, event):
        os._exit(0)

def start_menu():
    app = QApplication(sys.argv)
    ui = UI()

    app.exec()

def restart_script():
    python = sys.executable
    script = os.path.abspath(sys.argv[0])
    subprocess.Popen([python, script])
    os._exit(0)

def start_recording(bridge):
    recorder = microphone_recording(bridge, device_index)
    recorder.record()

if __name__ == "__main__":
    threading.Thread(target=start_menu, daemon=True).start()

    while bridge is None:
        pass

    start_recording(bridge)