import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import config
import stt
import tts
from fuzzywuzzy import fuzz
import datetime
import webbrowser
import random
import wikipediaapi
import re

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{config.VA_NAME} - Голосовой ассистент")
        self.root.geometry("700x650")
        self.root.configure(bg='#2c3e50')
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        
        # Заголовок
        title = tk.Label(root, text=f"{config.VA_NAME} v{config.VA_VER}", 
                         font=('Arial', 18, 'bold'), bg='#2c3e50', fg='#ecf0f1')
        title.pack(pady=10)
        
        # Область вывода сообщений (лог)
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=15,
                                                    font=('Consolas', 10), bg='#34495e', fg='white')
        self.log_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # ========== БЛОК ПОИСКА В ВИКИПЕДИИ (с озвучкой) ==========
        wiki_frame = tk.LabelFrame(root, text="🔍 Поиск в Википедии (с голосовым ответом)", 
                                   bg='#2c3e50', fg='white', font=('Arial', 10, 'bold'))
        wiki_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.wiki_entry = tk.Entry(wiki_frame, font=('Arial', 12), bg='#ecf0f1')
        self.wiki_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        wiki_btn = tk.Button(wiki_frame, text="Найти и озвучить", command=self.search_wikipedia,
                             bg='#3498db', fg='white', font=('Arial', 10), padx=10)
        wiki_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # ========== БЛОК ПОИСКА В ИНТЕРНЕТЕ ==========
        web_frame = tk.LabelFrame(root, text="🌐 Поиск в Интернете", bg='#2c3e50', fg='white', font=('Arial', 10, 'bold'))
        web_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.web_entry = tk.Entry(web_frame, font=('Arial', 12), bg='#ecf0f1')
        self.web_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        web_btn = tk.Button(web_frame, text="Поискать в Google", command=self.search_web,
                            bg='#27ae60', fg='white', font=('Arial', 10), padx=10)
        web_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # ========== КНОПКИ УПРАВЛЕНИЯ ==========
        btn_frame = tk.Frame(root, bg='#2c3e50')
        btn_frame.pack(pady=5)
        
        self.listen_btn = tk.Button(btn_frame, text="🎤 Слушать команду", command=self.start_listening,
                                    font=('Arial', 12), bg='#e74c3c', fg='white', padx=20, pady=5)
        self.listen_btn.pack(side=tk.LEFT, padx=5)
        
        quit_btn = tk.Button(btn_frame, text="❌ Выход", command=root.quit,
                             font=('Arial', 12), bg='#95a5a6', padx=20, pady=5)
        quit_btn.pack(side=tk.LEFT, padx=5)
        
        # Строка статуса
        self.status_label = tk.Label(root, text="Статус: Ожидание команды", 
                                     font=('Arial', 10), bg='#2c3e50', fg='#bdc3c7')
        self.status_label.pack(pady=5)
        
        # Инициализация API Википедии
        self.wiki = wikipediaapi.Wikipedia(
            language='ru',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='JarvisAssistant/2.0'
        )
        
        self.log("🚀 Ассистент запущен. Нажмите 'Слушать команду' или используйте поля поиска.")
        self.log("Примеры голосовых команд: 'Кеша, время', 'Кеша, найди в википедии Python', 'Кеша, погугли рецепт пиццы'")
        
    def log(self, message):
        """Вывод сообщения в лог-область"""
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.root.update()
        
    def update_status(self, text):
        self.status_label.config(text=f"Статус: {text}")
        self.root.update()
        
    def start_listening(self):
        """Запуск прослушивания микрофона в отдельном потоке"""
        self.listen_btn.config(state=tk.DISABLED, text="🎙️ Слушаю...")
        self.update_status("Слушаю вашу команду...")
        thread = threading.Thread(target=self.listen_and_respond)
        thread.daemon = True
        thread.start()
        
    def listen_and_respond(self):
        """Потоковая функция прослушивания"""
        try:
            def callback(voice):
                self.root.after(0, self.process_voice, voice)
            stt.va_listen(callback)   # предполагается, что stt.py содержит эту функцию
        except Exception as e:
            self.log(f"❌ Ошибка при прослушивании: {e}")
        finally:
            self.root.after(0, self.reset_button)
            
    def reset_button(self):
        self.listen_btn.config(state=tk.NORMAL, text="🎤 Слушать команду")
        self.update_status("Готов к работе")
        
    def process_voice(self, voice):
        """Обработка распознанной голосовой команды"""
        self.log(f"🎤 Вы сказали: {voice}")
        voice_lower = voice.lower()
        # Проверка, обращаются ли к ассистенту по имени
        if not any(alias.lower() in voice_lower for alias in config.VA_ALIAS):
            self.log("❌ Имя не распознано. Обратитесь ко мне по имени.")
            return
            
        # Очистка команды от алиасов и стоп-слов
        cmd_text = self.filter_cmd(voice)
        self.log(f"🔍 Обработанная команда: '{cmd_text}'")
        
        # Распознавание намерения (команды)
        cmd = self.recognize_cmd(cmd_text)
        self.log(f"📊 Распознавание: {cmd['cmd']} ({cmd['percent']}%)")
        
        if cmd['percent'] < 50:
            self.say("Не понял команду")
        else:
            self.execute_cmd(cmd['cmd'], voice)
            
    def filter_cmd(self, raw_voice):
        cmd = raw_voice.lower()
        for x in config.VA_ALIAS:
            cmd = cmd.replace(x.lower(), "").strip()
        for x in config.VA_TBR:
            cmd = cmd.replace(x.lower(), "").strip()
        return cmd
        
    def recognize_cmd(self, cmd):
        rc = {'cmd': '', 'percent': 0}
        for c, v in config.VA_CMD_LIST.items():
            for x in v:
                vrt = fuzz.ratio(cmd, x.lower())
                if vrt > rc['percent']:
                    rc['cmd'] = c
                    rc['percent'] = vrt
        return rc
        
    def say(self, text):
        """Озвучивание текста и запись в лог"""
        self.log(f"🤖 Ассистент: {text}")
        tts.va_speak(text)   # ВЫЗОВ ОЗВУЧКИ
        
    # ========== ПОИСК В ВИКИПЕДИИ С ОЗВУЧКОЙ ==========
    def search_wikipedia(self):
        """Поиск по текстовому полю с озвучиванием результата"""
        topic = self.wiki_entry.get().strip()
        if not topic:
            self.say("Введите тему для поиска в Википедии")
            return
        self.say(f"Ищу про {topic}")
        answer = self.get_wikipedia_summary(topic)
        self.say(answer)   # Озвучиваем найденное
        self.wiki_entry.delete(0, tk.END)
        
    def search_web(self):
        """Поиск в Google по текстовому полю"""
        query = self.web_entry.get().strip()
        if not query:
            self.say("Введите запрос для поиска в интернете")
            return
        self.say(f"Ищу в интернете: {query}")
        webbrowser.open(f"https://www.google.com/search?q={query}")
        self.web_entry.delete(0, tk.END)
        
    def execute_cmd(self, cmd, voice=""):
        if cmd == 'help':
            self.say("Я умею показывать время, рассказывать анекдоты, открывать браузер, искать в Википедии и в интернете.")
        
        elif cmd == 'ctime':
            from num2words import num2words
            now = datetime.datetime.now()
            text = f"Сейчас {num2words(now.hour, lang='ru')} часов {num2words(now.minute, lang='ru')} минут"
            self.say(text)
        
        elif cmd == 'joke':
            jokes = [
                'Программисты смеются: ехе ехе ехе',
                'SQL заходит в бар: можно присоединиться?',
                'Кофе - это код',
                'Почему программисты не любят природу? Слишком много багов'
            ]
            self.say(random.choice(jokes))
        
        elif cmd == 'open_browser':
            webbrowser.open("https://google.com")
            self.say("Открываю браузер")
        
        elif cmd == 'wikipedia':
            # Извлечение темы из голосовой фразы
            voice_lower = voice.lower()
            for alias in config.VA_ALIAS:
                voice_lower = voice_lower.replace(alias.lower(), "")
            stop_words = ['википедия', 'что такое', 'кто такой', 'расскажи о', 'найди в википедии', 'поищи в вики', 'вики']
            for word in stop_words:
                voice_lower = voice_lower.replace(word, "")
            topic = re.sub(r'[^\w\s]', '', voice_lower).strip()
            self.log(f"🔎 Тема для Википедии: '{topic}'")
            if topic and len(topic) > 2:
                self.say(f"Ищу про {topic}")
                answer = self.get_wikipedia_summary(topic)
                self.say(answer)   # ОЗВУЧКА РЕЗУЛЬТАТА ВИКИПЕДИИ
            else:
                self.say("Что найти в Википедии? Скажите, например: 'Кеша, найди в википедии Москва'")
        
        elif cmd == 'web_search':
            voice_lower = voice.lower()
            for alias in config.VA_ALIAS:
                voice_lower = voice_lower.replace(alias.lower(), "")
            stop_words = ['найди в интернете', 'поищи в гугл', 'найди в гугле', 'поиск', 'погугли', 'найди информацию о']
            for word in stop_words:
                voice_lower = voice_lower.replace(word, "")
            query = voice_lower.strip()
            self.log(f"🔎 Поисковый запрос: '{query}'")
            if query:
                self.say(f"Ищу в интернете: {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
            else:
                self.say("Что найти в интернете?")
                
    def get_wikipedia_summary(self, topic):
        """Получение краткого содержания статьи из Википедии"""
        try:
            topic = topic.lower().strip()
            page = self.wiki.page(topic)
            if not page.exists():
                return f"Не нашел статью про '{topic}'"
            summary = page.summary
            if len(summary) > 700:
                summary = summary[:700] + "..."
            return f"Вот что я нашел про {page.title}: {summary}"
        except Exception as e:
            return f"Ошибка при поиске в Википедии: {e}"

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()