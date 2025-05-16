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
import re
from PIL import Image
from deep_translator import GoogleTranslator
from gtts import gTTS
from config import GOOGLE_API_KEY, OPENWEATHER_API_KEY

# VLC path detection and configuration
def find_vlc_path():
    common_paths = [
        r'C:\Program Files\VideoLAN\VLC',
        r'C:\Program Files (x86)\VideoLAN\VLC',
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'VideoLAN', 'VLC'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'VideoLAN', 'VLC')
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None

# Try to find and configure VLC path
vlc_path = find_vlc_path()
if vlc_path:
    os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']
    if not os.path.exists(os.path.join(vlc_path, 'libvlc.dll')):
        print("Warning: VLC is installed but libvlc.dll not found in the expected location.")
else:
    print("Warning: VLC installation not found. Please install VLC Media Player.")

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
engine.setProperty('rate', 175)  # Speed of speech - increased from 150 to 175
engine.setProperty('volume', 1.0)  # Volume level

# Create a thread lock for the speech engine
speak_lock = threading.Lock()

# Global variables for music control
current_player = None
player_lock = threading.Lock()
current_song_title = None

def remove_emojis(text):
    """
    Remove emojis and other special characters from text.
    """
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

def speak(audio):
    with speak_lock:
        try:
            # Remove emojis before speaking
            clean_audio = remove_emojis(audio)
            print("Speaking:", clean_audio)  # Debug print
            engine.say(clean_audio)
            engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")
            time.sleep(0.5)
            try:
                engine.say(clean_audio)
                engine.runAndWait()
            except Exception as e:
                print(f"Second speech attempt failed: {e}")

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
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "photos": "ms-photos:",
    "mail": "outlookmail:",
    "calendar": "outlookcal:",
    "settings": "ms-settings:",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",
    "powershell": "powershell.exe",
    "windows media player": "wmplayer.exe",
    "snipping tool": "SnippingTool.exe",
    "sticky notes": "StickyNot.exe",
    "onenote": r"C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE",
    "teams": r"C:\Users\hp5cd\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "discord": r"C:\Users\hp5cd\AppData\Local\Discord\app-1.0.9003\Discord.exe",
    "zoom": r"C:\Users\hp5cd\AppData\Roaming\Zoom\bin\Zoom.exe",
    "adobe reader": r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
    "photoshop": r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
    "illustrator": r"C:\Program Files\Adobe\Adobe Illustrator 2023\Support Files\Contents\Windows\Illustrator.exe"
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

def translate_text(text, target_lang='en'):
    """
    Translates text to the specified target language.
    :param text: Text to translate
    :param target_lang: Target language code (e.g., 'es' for Spanish, 'fr' for French)
    :return: Translated text and source language
    """
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translation = translator.translate(text)
        return {
            'translated_text': translation,
            'source_lang': translator.source,
            'pronunciation': getattr(translator, 'pronunciation', None)
        }
    except Exception as e:
        return f"Translation error: {str(e)}"

def get_voice_for_language(language_code):
    """
    Get the appropriate voice for the specified language code.
    Returns the voice ID if found, otherwise returns the default voice.
    """
    voices = engine.getProperty('voices')
    
    # Map of language codes to common language identifiers in voice names
    language_identifiers = {
        'es': ['spanish', 'espanol', 'es-'],
        'fr': ['french', 'français', 'fr-'],
        'de': ['german', 'deutsch', 'de-'],
        'it': ['italian', 'italiano', 'it-'],
        'pt': ['portuguese', 'português', 'pt-'],
        'ru': ['russian', 'русский', 'ru-'],
        'ja': ['japanese', '日本語', 'ja-'],
        'ko': ['korean', '한국어', 'ko-'],
        'zh-cn': ['chinese', '中文', 'zh-'],
        'hi': ['hindi', 'हिंदी', 'hi-'],
    }
    
    # Get identifiers for the requested language
    identifiers = language_identifiers.get(language_code, [])
    
    # Try to find a matching voice
    for voice in voices:
        voice_name = voice.name.lower()
        if any(identifier.lower() in voice_name for identifier in identifiers):
            return voice.id
    
    # Return default voice if no match found
    return voices[1].id

def speak_with_gtts(text, lang='en'):
    """
    Speak text using Google Text-to-Speech with support for multiple languages.
    """
    try:
        # Remove emojis before generating speech
        clean_text = remove_emojis(text)
        
        # Create temporary file path
        temp_file = "temp_speech.mp3"
        
        # Generate speech
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        tts.save(temp_file)
        
        # Play the audio using VLC
        instance = vlc.Instance()
        player = instance.media_player_new()
        media = instance.media_new(temp_file)
        player.set_media(media)
        player.play()
        
        # Wait for audio to finish
        time.sleep(1)  # Give VLC time to start
        duration = 0
        while player.is_playing() and duration < 30:  # Timeout after 30 seconds
            time.sleep(0.1)
            duration += 0.1
            
        player.stop()
        
        # Clean up
        try:
            os.remove(temp_file)
        except:
            pass
            
    except Exception as e:
        print(f"gTTS speech error: {e}")
        # Fallback to regular speak function
        speak(clean_text)

def speak_translation(text, language_code='en'):
    """
    Speak translated text using gTTS for authentic accent in the target language.
    Always uses gTTS for translations to maintain native accent quality.
    """
    try:
        print(f"\nSpeaking translation in {language_code}")
        print(f"Text: {text}")
        speak_with_gtts(text, language_code)
    except Exception as e:
        print(f"Translation speech error: {e}")
        # Fallback to regular speak only for English
        if language_code == 'en':
            speak(text)



# Main logic
if __name__ == "__main__":
    greet_user()

    while True:
        query = takeCommand().lower()

        # Skip processing if the assistant couldn't understand the input
        if query == "none":
            continue

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

        elif "translate" in query:
            speak("What would you like me to translate?")
            text_to_translate = takeCommand()
            if text_to_translate != "None":
                speak("To which language should I translate? For example, say Hindi, Spanish, Japanese, etc.")
                target_language = takeCommand().lower()
                
                # Enhanced language code mapping with common variations
                language_codes = {
                    # Asian Languages
                    'hindi': 'hi',
                    'hindustani': 'hi',
                    'indian': 'hi',
                    'japanese': 'ja',
                    'chinese': 'zh-cn',
                    'mandarin': 'zh-cn',
                    'korean': 'ko',
                    'thai': 'th',
                    'vietnamese': 'vi',
                    
                    # Indian Regional Languages
                    'tamil': 'ta',
                    'telugu': 'te',
                    'malayalam': 'ml',
                    'kannada': 'kn',
                    'bengali': 'bn',
                    'marathi': 'mr',
                    'gujarati': 'gu',
                    'punjabi': 'pa',
                    'urdu': 'ur',
                    
                    # European Languages
                    'spanish': 'es',
                    'español': 'es',
                    'french': 'fr',
                    'français': 'fr',
                    'german': 'de',
                    'deutsch': 'de',
                    'italian': 'it',
                    'italiano': 'it',
                    'portuguese': 'pt',
                    'português': 'pt',
                    'russian': 'ru',
                    'dutch': 'nl',
                    'greek': 'el',
                    
                    # Middle Eastern Languages
                    'arabic': 'ar',
                    'persian': 'fa',
                    'farsi': 'fa',
                    'turkish': 'tr',
                    'hebrew': 'iw',
                    
                    # Other Languages
                    'english': 'en',
                    'indonesian': 'id',
                    'malay': 'ms',
                    'filipino': 'tl',
                    'tagalog': 'tl'
                }
                
                # Get the language code or use the spoken language name as code
                target_lang = language_codes.get(target_language, target_language)
                
                try:
                    # First, confirm the translation language
                    language_name = next((name for name, code in language_codes.items() if code == target_lang), target_lang)
                    speak(f"Translating to {language_name}")
                    
                    result = translate_text(text_to_translate, target_lang)
                    if isinstance(result, dict):
                        translated_text = result['translated_text']
                        source_lang = result['source_lang']
                        
                        print(f"\nOriginal ({source_lang}): {text_to_translate}")
                        print(f"Translated ({target_lang}): {translated_text}")
                        
                        # First announce in English what we're going to do
                        speak("Here's your translation")
                        time.sleep(0.5)  # Add a small pause
                        
                        # Then speak the translation in the target language with native accent
                        speak_translation(translated_text, target_lang)
                    else:
                        speak(result)  # This will be the error message
                except Exception as e:
                    speak(f"Sorry, I encountered an error while translating: {str(e)}")

        # Remove the specific chat triggers and make chat the default behavior
        elif any(keyword in query for keyword in [
            "exit", "stop", "weather", "time", "wikipedia", "open youtube",
            "play", "pause", "resume", "remember that", "do you remember",
            "who created you", "who made you", "how were you created", "who developed you"
        ]):
            continue  # Let the existing commands handle these queries
        else:
            # Any other query will be treated as a conversation with Gemini
            response = chat_with_gemini(f"Act as Vani, a friendly AI assistant. Respond to: {query}")
            print(response)
            speak(response)


