import datetime
import pytz
import requests
import pyttsx3
import speech_recognition as sr

# Initialize pyttsx3 engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def takeCommand():
    # It takes microphone input from the user and returns string output
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        r.energy_threshold = 300
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)

    try:
        print("Recognizing...")    
        query = r.recognize_google(audio, language='en-US')
        print(f"User said: {query}\n")

    except sr.UnknownValueError:
        print("Sorry, I couldn't understand that...")
        return "None"
    except sr.RequestError:
        print("Sorry, there was an error with the speech recognition service...")
        return "None"
    except Exception as e:
        print("Say that again please...")  
        return "None"
    return query

def get_weather(city_name):
    api_key = "6a2b433a42668ac64b73a1c16d12d531"  # Your API key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
    complete_url = f"{base_url}appid={api_key}&q={city_name}&units=metric"
    response = requests.get(complete_url)
    data = response.json()

    if data["cod"] != "404":
        weather_main = data["main"]
        temperature = weather_main["temp"]
        description = data["weather"][0]["description"]
        return f"{temperature}°C, {description.capitalize()}"
    else:
        return "Weather data not available!"

def greet_user():
    # 1. Hello master Vani here
    speak("Hello master Vani here")

    # 2. Present day
    today = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%A, %d %B %Y')
    speak(f"Today is: {today}")

    # 3. Present time according to India
    current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
    speak(f"Current time of awor location : {current_time}")

    # 4. Weather outside (real)
    city = "bhopal"  # you can change the city name
    weather = get_weather(city)
    speak(f"Weather in {city}: {weather}")

    # 5. How can I help you today?
    speak("How can I help you today?")

# Main function
if __name__ == "__main__":
    greet_user()

    # Listen for a command from the user
    query = takeCommand().lower()
    if "weather" in query:
        city = "Delhi"  # You can dynamically take the city name from the user
        weather_info = get_weather(city)
        speak(f"The current weather in {city} is {weather_info}")
    elif "time" in query:
        current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
        speak(f"The current time in India is {current_time}")
    else:
        speak("Sorry, I couldn't understand your request.")
