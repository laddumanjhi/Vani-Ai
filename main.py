import datetime
import pytz
import requests
import pyttsx3
import speech_recognition as sr
import wikipedia
import pyaudio
import subprocess
import webbrowser
import os

# Initialize pyttsx3 engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def takeCommand():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 1
        recognizer.energy_threshold = 300
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-US')
        print(f"User said: {query}")
        return query
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand that...")
        speak("Sorry, I didn't catch that.")
        return "None"
    except sr.RequestError:
        print("Speech recognition service error.")
        speak("There was an issue with the speech recognition service.")
        return "None"
    except Exception as e:
        print("Error:", e)
        speak("Say that again please.")
        return "None"

def get_weather(city_name):
    api_key = "6a2b433a42668ac64b73a1c16d12d531"  # Your API key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={api_key}&q={city_name}&units=metric"

    response = requests.get(complete_url)
    data = response.json()

    if data["cod"] != "404":
        temperature = data["main"]["temp"]
        description = data["weather"][0]["description"]
        return f"{temperature}°C, {description.capitalize()}"
    else:
        return "Weather data not available!"

def greet_user():
    speak("Hello master, Vani here")

    today = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%A, %d %B %Y')
    speak(f"Today is: {today}")

    current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
    speak(f"Current time of our location: {current_time}")

    city = "Bhopal"
    weather = get_weather(city)
    speak(f"Weather in {city}: {weather}")

    speak("How can I help you today?")

def search_wikipedia(query, sentences=2, lang='en'):
    try:
        wikipedia.set_lang(lang)
        summary = wikipedia.summary(query, sentences=sentences)
        return summary
    except wikipedia.DisambiguationError as e:
        return f"There are multiple results for '{query}': {', '.join(e.options[:3])}"
    except wikipedia.PageError:
        return f"I couldn't find any page for '{query}'."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def remember_thing(thing):
    with open("memory.txt", "w") as file:
        file.write(thing)
    speak("Okay, I will remember that.")

def recall_memory():
    try:
        with open("memory.txt", "r") as file:
            memory = file.read()
            if memory:
                speak(f"You asked me to remember: {memory}")
            else:
                speak("I don't have anything remembered right now.")
    except FileNotFoundError:
        speak("I don't have anything remembered yet.")

# Dictionary of applications and their paths
apps = {
    "notepad": "notepad.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "calculator": "calc.exe",
    "command prompt": "cmd.exe",
    "paint": "mspaint.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "vs code": r"C:\Users\hp5cd\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "code": r"C:\Users\hp5cd\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\hp5cd\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\hp5cd\AppData\Roaming\Spotify\Spotify.exe",
    "microsoft store": r"C:\Program Files\WindowsApps\Microsoft.WindowsStore_8wekyb3d8bbwe\WinStore.App.exe",
    "camera": "microsoft.windows.camera:",
    "anydesk": r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",
    "arc": r"C:\Program Files\Arc\Arc.exe",
    "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "cursor": r"C:\Program Files\WindowsApps\Microsoft.CursorExperience_1.0.0.0_x64__8wekyb3d8bbwe\CursorApp.exe",
    "davinci resolve": r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe",
    "figma": r"C:\Users\hp5cd\AppData\Local\Figma\Figma.exe",
    "github desktop": r"C:\Users\hp5cd\AppData\Local\GitHubDesktop\GitHubDesktop.exe",
    "intellij idea": r"C:\Program Files\JetBrains\IntelliJ IDEA 2023.2\bin\idea64.exe",
    "visual studio": r"C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
    "photoshop": r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
    "discord": r"C:\Users\hp5cd\AppData\Local\Discord\app-1.0.9014\Discord.exe",
    "zoom": r"C:\Users\hp5cd\AppData\Roaming\Zoom\bin\Zoom.exe",
    "slack": r"C:\Users\hp5cd\AppData\Local\slack\slack.exe",
    "teams": r"C:\Users\hp5cd\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "notion": r"C:\Users\hp5cd\AppData\Local\Notion\Notion.exe",
    "telegram": r"C:\Users\hp5cd\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "vscode": r"C:\Users\hp5cd\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "blender": r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    "audacity": r"C:\Program Files (x86)\Audacity\audacity.exe",
    "whatsapp": r"C:\Users\hp5cd\AppData\Local\WhatsApp\WhatsApp.exe"
}



def open_app(app_name):
    for key in apps:
        if key in app_name:
            try:
                subprocess.Popen(apps[key])
                speak(f"Opening {key}")
                return
            except Exception as e:
                speak(f"Sorry, I couldn't open {key}")
                print(f"Error opening {key}: {e}")
                return
    speak("Sorry, I couldn't find that application.")

# Main function
if __name__ == "__main__":
    greet_user()

    while True:
        query = takeCommand().lower()

        if "weather" in query:
            speak("Name of the city:")
            city = takeCommand()
            weather_info = get_weather(city)
            speak(f"The current weather in {city} is {weather_info}")

        elif "time" in query:
            current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
            speak(f"The current time in India is {current_time}")

        elif "wikipedia" in query:
            speak("What should I search on Wikipedia?")
            search_query = takeCommand()
            if search_query != "None":
                summary = search_wikipedia(search_query)
                print("\nSummary:\n", summary)
                speak(summary)
            else:
                speak("Sorry, I couldn't catch the topic to search.")

        elif "open youtube" in query:
            speak("Opening YouTube for you.")
            webbrowser.open("https://www.youtube.com")

        elif "open" in query:
            open_app(query)

        elif "exit" in query or "stop" in query:
            speak("Goodbye, have a great day!")
            break

        elif "remember that" in query:
            speak("What should I remember?")
            memory = takeCommand()
            if memory != "None":
                remember_thing(memory)
            else:
                speak("I couldn't catch that to remember.")

        elif "do you remember" in query or "what do you remember" in query:
            recall_memory()

        else:
            speak("Sorry, I couldn't understand your request. Please try again.")
