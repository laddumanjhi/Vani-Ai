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
import time
import yt_dlp
import vlc
import threading
import queue

# Initialize pyttsx3 engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

# Create a thread lock for the speech engine
speak_lock = threading.Lock()

# Global variables for music control
current_player = None
player_lock = threading.Lock()
current_song_title = None

def speak(audio):
    with speak_lock:
        try:
            engine.say(audio)
            engine.runAndWait()
        except RuntimeError:
            time.sleep(0.5)
            try:
                engine.say(audio)
                engine.runAndWait()
            except:
                print(f"Could not speak: {audio}")

def stop_current_song():
    global current_player, current_song_title
    with player_lock:
        if current_player:
            current_player.stop()
            current_player = None
            current_song_title = None

def pause_playback():
    global current_player
    with player_lock:
        if current_player:
            current_player.pause()
            return True
    return False

def resume_playback():
    global current_player
    with player_lock:
        if current_player:
            current_player.play()
            return True
    return False

def get_playback_status():
    global current_player, current_song_title
    with player_lock:
        if current_player:
            state = current_player.get_state()
            if state == vlc.State.Playing:
                return f"Playing: {current_song_title}"
            elif state == vlc.State.Paused:
                return f"Paused: {current_song_title}"
            else:
                return "No song is currently playing"
        return "No song is currently playing"

def play_song_from_youtube(song_name):
    global current_player, current_song_title
    
    # Stop any currently playing song
    stop_current_song()
    
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        
        # Search for the song
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Searching for song...")
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)['entries'][0]
            url = info.get('url')
            title = info.get('title')
            
            if not url:
                print("Could not get song URL")
                speak("Sorry, I couldn't find that song")
                return
                
            print(f"\nPlaying: {title}")
            speak(f"Playing {title}")
            current_song_title = title
            
            # Create and start the media player in a separate thread
            def play_audio():
                global current_player
                with player_lock:
                    instance = vlc.Instance()
                    current_player = instance.media_player_new()
                    media = instance.media_new(url)
                    current_player.set_media(media)
                    current_player.play()
                
                # Monitor playback
                time.sleep(2)  # Give VLC time to start
                while True:
                    with player_lock:
                        if not current_player:
                            break
                        state = current_player.get_state()
                        if state in [vlc.State.Ended, vlc.State.Error, vlc.State.Stopped]:
                            current_player = None
                            current_song_title = None
                            break
                    time.sleep(1)
            
            # Start playback thread
            play_thread = threading.Thread(target=play_audio)
            play_thread.daemon = True
            play_thread.start()
            
    except Exception as e:
        print(f"Error playing song: {e}")
        speak("Sorry, I couldn't play that song")

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
        speak("I didn't understand that. Could you please repeat?")
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
    api_key = "6a2b433a42668ac64b73a1c16d12d531"
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

apps = {
    "notepad": "notepad.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "calculator": "calc.exe",
    "cmd": "cmd.exe",
    "paint": "mspaint.exe",
    "spotify": r"C:\Users\hp5cd\AppData\Roaming\Spotify\Spotify.exe",
    "vs code": r"C:\Users\hp5cd\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
    # Add more apps as needed
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

# Main logic
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

        elif query.startswith("play"):
            song_name = query.replace("play", "").replace("song", "").replace("on youtube", "").strip()
            if song_name:
                play_song_from_youtube(song_name)
            else:
                speak("Which song should I play?")
                song_name = takeCommand()
                if song_name != "None":
                    play_song_from_youtube(song_name)

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

        elif "pause" in query or "pause music" in query or "pause song" in query:
            if pause_playback():
                speak("Playback paused")
            else:
                speak("No song is currently playing")

        elif "resume" in query or "resume music" in query or "resume song" in query:
            if resume_playback():
                speak("Resuming playback")
            else:
                speak("No song is paused")

        elif "stop music" in query or "stop song" in query:
            stop_current_song()
            speak("Music stopped")

        elif "what's playing" in query or "what song is playing" in query or "current song" in query:
            status = get_playback_status()
            speak(status)


