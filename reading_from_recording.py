import datetime
import random
import threading

import pygame
import subprocess
import os
import psutil
import pyautogui

import webbrowser
import urllib.parse

from assets.read_files import read_file

class read_from_record:
    def __init__(self, read_json_file):
        self.read_settings = read_json_file.read_json_file('settings')

        self.assistant = self.read_settings['assistant']

        self.file_audio = f'audio/{self.assistant}'

        self.answer = {f'{self.file_audio}/ok_1.wav', f'{self.file_audio}/ok_2.wav', f'{self.file_audio}/ok_3.wav', f'{self.file_audio}/ok_4.wav'}
        self.thanks = f'{self.file_audio}/thanks.wav'

        self.settings = read_json_file.read_json_file('config')

        # Список распространенных имен процессов браузеров
        self.browser_process_names = [
            "chrome.exe",    # Google Chrome (Windows)
            "firefox.exe",   # Mozilla Firefox (Windows)
            "msedge.exe",    # Microsoft Edge (Windows)
            "opera.exe",     # Opera (Windows)
            "browser.exe",   # Yandex Browser (Windows)
        ]

        self.new_commands_close = []

        pygame.mixer.init() # Инициализация pygame.mixer один раз

    def play_sound(self, file_name):
        try:
            pygame.mixer.music.load(file_name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(30)
        except pygame.error: pass
        finally: pygame.mixer.music.stop()

    def find_file(self, filename, search_path):
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        
        return None

    def open_program(self, filename, disk):
        file_path = self.find_file(filename, disk)

        if file_path:
            self.log(f'Файл найден: {file_path}')

            try:
                subprocess.Popen(file_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                self.log(f'Ошибка при запуске файла: {e}')
        else:
            self.play_sound(f'{self.file_audio}/error.wav')

    def close_program(self, name_process):
        for proc in psutil.process_iter():
            try:
                # Получаем имя процесса (приводим к нижнему регистру для кросс-платформенности)
                process_name = proc.name().lower()
                if process_name in name_process:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def react(self, text):
        opens = self.settings["cmds"]["opens"]
        closes = self.settings["cmds"]["closes"]

        read_commands = read_file()
        read_commands = read_commands.read_json_file('commands')

        if text in self.settings["cmds"]["thanks"]['words']:
            return self.play_sound(self.thanks)
        elif text in opens["taskmgr"]:
            self.play_sound(random.choice(list(self.answer)))
            return os.system('taskmgr')
        elif text in closes["taskmgr"]:
            self.play_sound(random.choice(list(self.answer)))
            return threading.Thread(target=self.close_program, args=("taskmgr.exe", )).start()
        elif text in opens["screenshot"]:
            if not os.path.exists("screenshot"):
                os.makedirs("screenshot")
            self.play_sound(random.choice(list(self.answer)))
            data = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            screenshot = pyautogui.screenshot()
            return screenshot.save(f'screenshot/screenshot_{data}.png')
        elif any(text.startswith(cmd) for cmd in opens["browser"]):  #elif text in opens["browser"]:
            self.play_sound(random.choice(list(self.answer)))
            if 'найди' in text:
                search_query = text.split('найди')[1].strip()
                if search_query:
                    encoded_query = urllib.parse.quote(search_query)
                    search_url = f'https://www.google.com/search?q={encoded_query}'
                    webbrowser.open(search_url)
                else:
                    webbrowser.open('https://www.google.com')
            else:
                webbrowser.open('https://www.google.com')
            return
        elif text in closes["browser"]:
            self.play_sound(random.choice(list(self.answer)))
            return threading.Thread(target=self.close_program, args=(self.browser_process_names, )).start() #self.close_program(self.browser_process_names)


        for name, details in read_commands.items():
            words = [word.strip() for word in details['word'].split(', ')]
            if text in words:
                try:
                    self.play_sound(random.choice(list(self.answer)))
                    if details['url']:
                        webbrowser.open(details['url'])
                    else:
                        new_program = None
                        if details['program'].startswith('steam://'):
                            threading.Thread(target=lambda: subprocess.run(['start', details['program']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)).start()
                            found = False
                            while not found:
                                for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
                                    try:
                                        if '-steam' in proc.info['cmdline']:
                                            new_program = proc.info['name'].lower()
                                            if any(name_program == new_program for name_program, _ in self.new_commands_close):
                                               self.log('Программа уже запущена!')
                                               continue
                                            found = True
                                            break
                                    except: pass
                                
                                if found == False and not new_program is None:
                                    new_program = None
                                    found = True
                        else:
                            threading.Thread(target=lambda: subprocess.Popen(details['program'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)).start()
                            new_program = (details['program'].split('\\')[-1]).lower()
                        
                        if new_program:

                            new_words = [word.replace('открой', 'закрой').replace('запусти', 'выключи') for word in words]
                            
                            if self.new_commands_close:
                                if not details['program'].startswith('steam://'):
                                    new_program = (details['program'].split('\\')[-1]).lower()
                                if not any(program.lower() == new_program for program, _ in self.new_commands_close):
                                    self.new_commands_close.append((new_program, new_words))
                            else:
                                self.new_commands_close.append((new_program, new_words))
                            print(self.new_commands_close)
                except Exception as e:
                    self.play_sound(f'{self.file_audio}/error.wav')
                    print(e)
                return

        if self.new_commands_close:
            for program, details in self.new_commands_close:
                # print(program, details)
                if text in details:
                    self.play_sound(random.choice(list(self.answer)))
                    threading.Thread(target=self.close_program, args=(program, )).start()
                    #self.close_program(program)
                    self.new_commands_close.remove((program, details))
                    print(self.new_commands_close)
                    return    

    def log(self, text):
        if text:
            time = datetime.datetime.now()
            print(f'[{time.hour:02}:{time.minute:02}:{time.second:02}] [log] {text}')
            self.react(text)


    def read_from_record(self, text):
        self.log(text)