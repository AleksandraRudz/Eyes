import config
import stt
import tts
from fuzzywuzzy import fuzz
import datetime
import webbrowser
import random
import wikipediaapi
import re

print(f"{config.VA_NAME} (v{config.VA_VER}) начал свою работу ...")

# Инициализация Википедии
wiki = wikipediaapi.Wikipedia(
    language='ru',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent='JarvisAssistant/2.0'
)

def get_wikipedia_summary(topic: str):
    try:
        topic = topic.lower().strip()
        page = wiki.page(topic)
        
        if not page.exists():
            return f"Не нашел статью про '{topic}'"
        
        summary = page.summary
        if len(summary) > 700:
            summary = summary[:700] + "..."
        
        return f"Вот что я нашел про {page.title}: {summary}"
    except Exception as e:
        return f"Ошибка: {e}"

def execute_cmd(cmd: str, voice: str = ""):
    if cmd == 'help':
        text = "Я умею показывать время, рассказывать анекдоты, открывать браузер, искать в Википедии"
        tts.va_speak(text)
    
    elif cmd == 'ctime':
        from num2words import num2words
        now = datetime.datetime.now()
        text = f"Сейчас {num2words(now.hour, lang='ru')} часов {num2words(now.minute, lang='ru')} минут"
        print(f"⏰ {text}")
        tts.va_speak(text)
    
    elif cmd == 'joke':
        jokes = [
            'Программисты смеются: ехе ехе ехе',
            'SQL заходит в бар: можно присоединиться?',
            'Кофе - это код',
            'Почему программисты не любят природу? Слишком много багов'
        ]
        tts.va_speak(random.choice(jokes))
    
    elif cmd == 'open_browser':
        webbrowser.open("https://google.com")
        tts.va_speak("Открываю браузер")
    
    elif cmd == 'wikipedia':
        voice_lower = voice.lower()
        for alias in config.VA_ALIAS:
            voice_lower = voice_lower.replace(alias.lower(), "")
        
        stop_words = ['википедия', 'что такое', 'кто такой', 'расскажи о', 'найди в википедии']
        for word in stop_words:
            voice_lower = voice_lower.replace(word, "")
        
        topic = re.sub(r'[^\w\s]', '', voice_lower).strip()
        
        if topic and len(topic) > 2:
            tts.va_speak(f"Ищу про {topic}")
            answer = get_wikipedia_summary(topic)
            tts.va_speak(answer)
        else:
            tts.va_speak("Что найти в Википедии?")

def va_respond(voice: str):
    print(f"🎤 Распознано: '{voice}'")
    
    voice_lower = voice.lower()
    found_alias = any(alias.lower() in voice_lower for alias in config.VA_ALIAS)
    
    if not found_alias:
        print("❌ Имя не распознано")
        return
    
    cmd_text = filter_cmd(voice)
    print(f"🔍 Обработанная команда: '{cmd_text}'")
    
    cmd = recognize_cmd(cmd_text)
    print(f"📊 Распознавание: {cmd['cmd']} ({cmd['percent']}%)")
    
    if cmd['percent'] < 50:
        tts.va_speak("Не понял")
    else:
        execute_cmd(cmd['cmd'], voice)

def filter_cmd(raw_voice: str):
    cmd = raw_voice.lower()
    for x in config.VA_ALIAS:
        cmd = cmd.replace(x.lower(), "").strip()
    for x in config.VA_TBR:
        cmd = cmd.replace(x.lower(), "").strip()
    return cmd

def recognize_cmd(cmd: str):
    rc = {'cmd': '', 'percent': 0}
    for c, v in config.VA_CMD_LIST.items():
        for x in v:
            vrt = fuzz.ratio(cmd, x.lower())
            if vrt > rc['percent']:
                rc['cmd'] = c
                rc['percent'] = vrt
    return rc

if stt.init_stt():
    print("🚀 Ассистент запущен")
    print("Пример: 'Кеша, время'")
    stt.va_listen(va_respond)
else:
    print("❌ Ошибка STT")