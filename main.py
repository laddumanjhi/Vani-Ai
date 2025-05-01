import datetime
import pytz
import requests
import pyttsx3
import speech_recognition as sr
import wikipedia
import pyaudio

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

    city = "Bhopal"  # You can change this
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
