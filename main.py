import pyttsx3
import speech_recognition as sr

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
# print(voices[1].id)
engine.setProperty('voice', voices[1].id)


def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def takeCommand():
    #It takes microphone input from the user and returns string output

    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        # Add energy threshold and dynamic ambient noise adjustment
        r.energy_threshold = 300
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)

    try:
        print("Recognizing...")    
        # Change language to generic English for better recognition
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


if __name__ == "__main__":

    Query = takeCommand()
    speak(Query)