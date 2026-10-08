```python
import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import os
import urllib.parse
import datetime
import sys

# ============================================================
# MAX - Voice + Text Desktop Assistant
# ============================================================

APP_NAME = "MAX"

# -----------------------------
# Text-to-Speech
# -----------------------------

engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)


def speak(text):
    print(f"MAX: {text}")
    engine.say(text)
    engine.runAndWait()


# -----------------------------
# Open Google Chrome
# -----------------------------

def open_chrome(url=None):
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]

    chrome = None

    for path in chrome_paths:
        if os.path.exists(path):
            chrome = path
            break

    if chrome:
        if url:
            subprocess.Popen([chrome, url])
        else:
            subprocess.Popen([chrome])
    else:
        # Fallback to default browser
        if url:
            webbrowser.open(url)
        else:
            webbrowser.open("https://www.google.com")


# -----------------------------
# Voice Recognition
# -----------------------------

def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )
        except sr.WaitTimeoutError:
            print("No voice detected.")
            return ""

    try:
        command = recognizer.recognize_google(audio)
        print(f"You: {command}")
        return command.lower()

    except sr.UnknownValueError:
        speak("Sorry, I could not understand that.")
        return ""

    except sr.RequestError:
        speak("Voice recognition is currently unavailable.")
        return ""


# -----------------------------
# Open websites
# -----------------------------

def open_website(site):
    websites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "whatsapp": "https://web.whatsapp.com",
        "linkedin": "https://www.linkedin.com",
        "chatgpt": "https://chatgpt.com",
        "stackoverflow": "https://stackoverflow.com"
    }

    site = site.lower().strip()

    if site in websites:
        open_chrome(websites[site])
        speak(f"Opening {site}")
        return True

    # If user gives a full URL
    if site.startswith("http://") or site.startswith("https://"):
        open_chrome(site)
        speak("Opening the website.")
        return True

    return False


# -----------------------------
# Google Search
# -----------------------------

def google_search(query):
    encoded = urllib.parse.quote_plus(query)

    url = f"https://www.google.com/search?q={encoded}"

    open_chrome(url)

    speak(f"Searching Google for {query}")


# -----------------------------
# YouTube Search
# -----------------------------

def youtube_search(query):
    encoded = urllib.parse.quote_plus(query)

    url = f"https://www.youtube.com/results?search_query={encoded}"

    open_chrome(url)

    speak(f"Searching YouTube for {query}")


# -----------------------------
# Command Processor
# -----------------------------

def process_command(command):

    if not command:
        return True

    command = command.lower().strip()

    # -------------------------
    # Exit
    # -------------------------

    if command in [
        "exit",
        "quit",
        "stop",
        "close max",
        "goodbye",
        "shutdown"
    ]:
        speak("Goodbye.")
        return False

    # -------------------------
    # Help
    # -------------------------

    if command in ["help", "what can you do"]:
        speak(
            "I can open Chrome, search Google, search YouTube, "
            "open websites, tell the time, and perform basic commands."
        )
        return True

    # -------------------------
    # Time
    # -------------------------

    if "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")
        return True

    # -------------------------
    # Open Chrome
    # -------------------------

    if command in [
        "open chrome",
        "start chrome",
        "launch chrome"
    ]:
        speak("Opening Chrome.")
        open_chrome()
        return True

    # -------------------------
    # Open websites
    # -------------------------

    if command.startswith("open "):

        website = command[5:].strip()

        if open_website(website):
            return True

        # Example:
        # "open python.org"

        if "." in website:
            if not website.startswith("http"):
                website = "https://" + website

            open_chrome(website)
            speak("Opening the website.")
            return True

    # -------------------------
    # Google Search
    # -------------------------

    search_prefixes = [
        "search google for ",
        "google search ",
        "search for ",
        "search "
    ]

    for prefix in search_prefixes:

        if command.startswith(prefix):

            query = command[len(prefix):].strip()

            if query:
                google_search(query)

            return True

    # -------------------------
    # YouTube
    # -------------------------

    youtube_prefixes = [
        "search youtube for ",
        "youtube search ",
        "play "
    ]

    for prefix in youtube_prefixes:

        if command.startswith(prefix):

            query = command[len(prefix):].strip()

            if query:
                youtube_search(query)

            return True

    # -------------------------
    # Direct YouTube opening
    # -------------------------

    if "open youtube" in command:

        open_chrome("https://www.youtube.com")
        speak("Opening YouTube.")
        return True

    # -------------------------
    # Google
    # -------------------------

    if "open google" in command:

        open_chrome("https://www.google.com")
        speak("Opening Google.")
        return True

    # -------------------------
    # Unknown command
    # -------------------------

    speak(
        "I don't know that command yet. "
        "Try saying search Google for something."
    )

    return True


# -----------------------------
# Text Mode
# -----------------------------

def text_mode():

    print("\n==============================")
    print("        MAX TEXT MODE")
    print("==============================")
    print("Type 'help' for commands.")
    print("Type 'exit' to close MAX.")

    while True:

        command = input("\nYou: ")

        if not process_command(command):
            break


# -----------------------------
# Voice Mode
# -----------------------------

def voice_mode():

    speak("MAX voice mode activated.")

    while True:

        command = listen()

        if command:

            if not process_command(command):
                break


# -----------------------------
# Main Program
# -----------------------------

def main():

    print("\n================================")
    print("          MAX ASSISTANT")
    print("================================")
    print("1. Text mode")
    print("2. Voice mode")
    print("3. Exit")

    while True:

        choice = input("\nSelect mode: ").strip()

        if choice == "1":
            text_mode()

        elif choice == "2":
            voice_mode()

        elif choice == "3":
            speak("Goodbye.")
            sys.exit()

        else:
            print("Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()
```
