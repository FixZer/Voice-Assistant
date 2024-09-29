import speech_recognition as sr
from reading_from_recording import *
from assets.read_files import *

import time
import gc

class microphone_recording:
    def __init__(self, bridge, device_index):
        self.is_listening = False
        self.silence_start_time = time.time()
        self.silence_timeout = 10
        self.recognizer = sr.Recognizer()
        self.microphone  = sr.Microphone(device_index=device_index)
        self.bridge = bridge
        self.gc_interval = 600
        self.last_gc_time = time.time()

    def start_record(self, read, assistant):
        self.is_listening = True
        self.bridge.set_active_assistant(self.is_listening)
        self.silence_start_time = time.time()
        return read.play_sound(f'audio/{assistant}/response_{random.randint(1, 3)}.wav')

    def stop_record(self, read, assistant):
        self.is_listening = False
        self.bridge.set_active_assistant(self.is_listening)
        return read.play_sound(f'audio/{assistant}/off.wav')

    def record(self):
        read_settings = read_file()
        read = read_from_record(read_settings)

        read_settings = read_settings.read_json_file('settings')

        address = read_settings['address'].lower()
        assistant = read_settings['assistant'].lower()
        turn_off = read_settings['turn_off'].lower()

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source) #duration=1
            print("Голосовой помощник начал свою работу!")
            read.play_sound(f'audio/{assistant}/hello_{random.randint(1, 2)}.wav')
            while True:
                try:
                    audio = self.recognizer.listen(source, timeout=1.5, phrase_time_limit=15) # timeout=5 phrase_time_limit=6
                    text_information =  self.recognizer.recognize_google(audio, language='ru-RU').lower()
                    if text_information:
                        if not self.is_listening:
                            if address in text_information:
                                threading.Thread(target=self.start_record, args=(read, assistant, )).start()
                        else:
                            if turn_off in text_information:
                                threading.Thread(target=self.stop_record, args=(read, assistant, )).start()
                            else:
                                threading.Thread(target=read.read_from_record, args=(text_information, )).start()
                                #read.read_from_record(text_information)
                                self.silence_start_time = time.time()
                except sr.WaitTimeoutError: # Если звука нет
                    if self.is_listening:
                        if time.time() - self.silence_start_time > self.silence_timeout:
                            self.is_listening = False
                            self.bridge.set_active_assistant(self.is_listening)
                            read.play_sound(f'audio/{assistant}/off.wav')
                except sr.UnknownValueError: pass #Не удалось распознать звук
                except sr.RequestError as e:
                    print(f'Не удалось запросить результаты от службы распознавания речи Google: {e}')
                except Exception as e:
                    print(f'Неожиданная ошибка: {e}')
                
                if time.time() - self.last_gc_time > self.gc_interval:
                    gc.collect()
                    self.last_gc_time = time.time()
