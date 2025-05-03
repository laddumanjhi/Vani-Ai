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
import google.generativeai as genai
import PyPDF2
import pyautogui
import pytesseract
from PIL import Image
from config import GOOGLE_API_KEY, OPENWEATHER_API_KEY

def check_tesseract_installation():
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Tesseract-OCR', 'tesseract.exe')
    ]
    
    # First check if tesseract is in PATH
    from shutil import which
    tesseract_cmd = which('tesseract')
    if tesseract_cmd:
        return tesseract_cmd
        
    # Then check common installation paths
    for path in common_paths:
        if os.path.isfile(path):
            return path
            
    return None

# Try to find and configure Tesseract path
tesseract_path = check_tesseract_installation()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Gemini API configuration
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Initialize chat history
chat_history = []

def chat_with_gemini(prompt):
    try:
        # Add personality and context to the prompt
        system_prompt = """You are Vani, a friendly and helpful AI assistant with a warm personality. 
        You engage in natural conversation while also being able to help with tasks. 
        Keep responses concise and conversational. If you're not sure about something, just say so."""
        
        # Maintain conversation context
        chat_history.append(prompt)
        if len(chat_history) > 10:  # Keep last 10 exchanges for context
            chat_history.pop(0)
        
        context_prompt = f"{system_prompt}\n\nRecent conversation context:\n{' -> '.join(chat_history[-3:])}\n\nCurrent query: {prompt}"
        
        response = model.generate_content(context_prompt)
        chat_history.append(response.text)  # Store response in history
        
        return response.text
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

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
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={OPENWEATHER_API_KEY}&q={city_name}&units=metric"
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

def read_file(file_path):
    try:
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                print("\n--- Text File Content ---\n")
                print(content)
                speak("Here's the content of your text file")
                speak(content)

        elif file_path.endswith('.pdf'):
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                print("\n--- PDF File Content ---\n")
                speak("Reading your PDF file")
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    print(f"\n--- Page {page_num + 1} ---\n")
                    print(text)
                    speak(f"Page {page_num + 1}")
                    speak(text)

        else:
            message = "Unsupported file type. Please provide a .txt or .pdf file."
            print(message)
            speak(message)
    except Exception as e:
        error_message = f"Error reading file: {str(e)}"
        print(error_message)
        speak(error_message)

def read_screen_text():
    if not tesseract_path:
        error_message = """Tesseract OCR is not installed or not found. Please follow these steps:
        1. Download Tesseract OCR installer from: https://github.com/UB-Mannheim/tesseract/wiki
        2. Run the installer
        3. Make sure to check 'Add to PATH' during installation
        4. Restart the application"""
        print(error_message)
        speak("Tesseract OCR is not installed. Please install it first.")
        return

    try:
        speak("Taking a screenshot to read text")
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        
        # Save the screenshot temporarily
        temp_image_path = "temp_screenshot.png"
        screenshot.save(temp_image_path)
        
        try:
            # Use OCR to extract text
            text = pytesseract.image_to_string(Image.open(temp_image_path))
            
            if text.strip():
                print("\n--- Text Found on Screen ---\n")
                print(text)
                speak("Here's the text I found on your screen")
                speak(text)
            else:
                message = "No readable text found on the screen"
                print(message)
                speak(message)
                
        finally:
            # Always try to remove the temporary file
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            
    except Exception as e:
        error_message = f"Error reading screen text: {str(e)}"
        print(error_message)
        speak(error_message)

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

        elif "tell me a joke" in query or "make me laugh" in query:
            response = chat_with_gemini("Tell me a family-friendly joke")
            print(response)
            speak(response)

        elif "let's chat" in query or "can we talk" in query:
            speak("Sure! What would you like to talk about?")
            chat_topic = takeCommand()
            if chat_topic != "None":
                response = chat_with_gemini(f"Let's have a friendly conversation about: {chat_topic}")
                print(response)
                speak(response)

        elif "ask gemini" in query:
            speak("What would you like to ask?")
            user_question = takeCommand()
            if user_question != "None":
                response = chat_with_gemini(user_question)
                print(response)
                speak(response)

        elif any(phrase in query for phrase in ["who created you", "who made you", "how were you created", "who developed you"]):
            creator_response = "I was created by Veerendra Vishwakarma, also known as The Codex. He is a talented developer who built me to be a helpful AI assistant."
            print(creator_response)
            speak(creator_response)

        elif "read file" in query:
            speak("Please provide the path to the file you want me to read")
            file_path = takeCommand()
            if file_path != "None":
                read_file(file_path)

        elif "read screen" in query or "read screen text" in query or "read my screen" in query:
            read_screen_text()

        # Remove the specific chat triggers and make chat the default behavior
        elif any(keyword in query for keyword in [
            "exit", "stop", "weather", "time", "wikipedia", "open youtube",
            "play", "pause", "resume", "remember that", "do you remember",
            "who created you", "who made you", "how were you created", "who developed you"
        ]):
            continue  # Let the existing commands handle these queries
        else:
            # Any other query will be treated as a conversation with Gemini
            if query != "None":
                response = chat_with_gemini(f"Act as Vani, a friendly AI assistant. Respond to: {query}")
                print(response)
                speak(response)


