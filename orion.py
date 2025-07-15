# orion.py - ORION: Omniscient Responsive Intelligent Operational Network

import logging
import random
import threading
import time as system_time
import warnings
from datetime import datetime, timedelta
from collections import deque

import pyttsx3
import spacy
import speech_recognition as sr
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

# Suppress warnings
warnings.filterwarnings("ignore")

# Logging
logging.basicConfig(filename="orion.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize core
engine = pyttsx3.init()
recognizer = sr.Recognizer()
nlp = spacy.load("en_core_web_sm")
nltk.download('punkt')

# Global states
focus_mode = False
focus_start = None
history = deque(maxlen=20)

# User Preferences
user = {
    "name": "User",
    "speech_rate": 150,
    "volume": 1.0,
    "language": "en-US",
    "goals": {"daily_tasks": 5, "focus_sessions": 3}
}

# Setup TTS engine
engine.setProperty('rate', user["speech_rate"])
engine.setProperty('volume', user["volume"])

# ML Intent Classifier
commands = [
    "set alarm", "set reminder", "start timer", "start focus mode", "stop focus mode",
    "schedule meeting", "show productivity", "show schedule", "exit", "what time is it"
]
labels = [c.split()[0] for c in commands]
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(commands)
model = LogisticRegression()
model.fit(X, labels)

# Speak

def speak(text):
    print("ORION:", text)
    engine.say(text)
    engine.runAndWait()

# Listen

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio, language=user["language"]).lower()
        except:
            speak("I didn't catch that.")
            return None

# Parse Duration

def parse_duration(text):
    if "minute" in text:
        return int(text.split()[0]) * 60
    elif "second" in text:
        return int(text.split()[0])
    return 1500

# Format Time

def fmt(dt):
    return dt.strftime("%I:%M %p")

# Time Management
reminders, alarms, timers, meetings = [], {}, {}, {}

def set_reminder(text, when):
    reminders.append({"text": text, "time": when, "done": False})
    speak(f"Reminder set for {fmt(when)}: {text}")

def set_alarm(name, when):
    alarms[name] = {"time": when, "active": True}
    speak(f"Alarm {name} set for {fmt(when)}")

def start_timer(name, duration):
    end = datetime.now() + timedelta(seconds=duration)
    timers[name] = {"end": end, "active": True}
    speak(f"Timer '{name}' started for {duration//60} minutes")

def schedule_meeting(name, when):
    meetings[name] = {"time": when, "notified": False}
    speak(f"Meeting '{name}' scheduled at {fmt(when)}")

def start_focus(duration=1500):
    global focus_mode, focus_start
    focus_mode = True
    focus_start = datetime.now()
    speak(f"Focus mode started for {duration//60} minutes")
    threading.Thread(target=stop_focus_after, args=(duration,), daemon=True).start()

def stop_focus_after(secs):
    global focus_mode
    system_time.sleep(secs)
    focus_mode = False
    duration = datetime.now() - focus_start
    speak(f"Focus ended. You focused for {duration.seconds//60} minutes.")

def process(cmd):
    vec = vectorizer.transform([cmd])
    intent = model.predict(vec)[0]
    return intent

def execute(cmd):
    intent = process(cmd)
    now = datetime.now()

    if "time" in cmd:
        speak(f"It's {fmt(now)}")
    elif intent == "alarm":
        speak("Set alarm for when?")
        t = listen()
        if t:
            set_alarm("alarm1", now + timedelta(minutes=1))
    elif intent == "reminder":
        speak("What to remind?")
        txt = listen()
        speak("When?")
        set_reminder(txt, now + timedelta(minutes=1))
    elif intent == "timer":
        speak("How long?")
        d = listen()
        start_timer("timer1", parse_duration(d))
    elif intent == "focus":
        start_focus()
    elif intent == "meeting":
        schedule_meeting("project", now + timedelta(minutes=2))
    elif intent == "schedule":
        speak("Here's your schedule.")
    elif intent == "productivity":
        speak("You completed 2 focus sessions today.")
    elif intent == "exit":
        speak("Goodbye!")
        exit()
    else:
        speak("Sorry, I didn’t understand that.")

# Main Loop

def main():
    speak(f"Hello {user['name']}, I'm ORION. How can I assist?")
    while True:
        cmd = listen()
        if cmd:
            execute(cmd)

if __name__ == "__main__":
    main()
