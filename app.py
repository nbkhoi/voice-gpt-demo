import re
from datetime import datetime
import pyttsx3
import speech_recognition as sr
from openai import OpenAI
# Use the OPENAI_API_KEY environment variable in the .env file
from pydub import AudioSegment
import simpleaudio as sa
from dotenv import load_dotenv
load_dotenv()
microphone = sr.Microphone()
recognizer = sr.Recognizer()
engine = pyttsx3.init(driverName='sapi5', debug=True)
client = OpenAI()


def recognize_speech_from_mic():
    with microphone as source:
        attempt = 0
        while attempt < 3:
            attempt = attempt + 1
            try:
                print(f"Attempt {attempt}")
                print("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source)
                print("Listening...")
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=2)
                # recognized_text = recognizer.recognize_whisper(audio, model='medium.en', language="en")
                # print(f"You said: {recognized_text}")
                recognized_file_name = f"audio{re.sub(r'[^0-9]', '', datetime.now().isoformat().lower())}.wav"
                with open(recognized_file_name, "wb") as f:
                    f.write(audio.get_wav_data())
                with open(recognized_file_name, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language="en"
                    )
                # transcription not blank
                if transcription and transcription.text != "":
                    print(f"Transcription: {transcription}")
                    return transcription
                else:
                    print("No transcription.")
                    raise sr.WaitTimeoutError
            except sr.WaitTimeoutError:
                if attempt < 3:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                                    {
                                        "role": "system",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "You are a voice chatbot work as a professional and patient "
                                                        "English learning assistant. You are waiting for a speech "
                                                        "form user and it's long enough for a kindly reminder. Your "
                                                        "task is that to generate a reminder to push user say "
                                                        "something."
                                            }
                                        ]
                                    },
                                    {
                                        "role": "assistant",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "Hello, I am your assistant. How can I help you?"
                                            }
                                        ]
                                    }
                                ])
                    content = response.choices[0].message.content
                    # engine.say(content)
                    # engine.runAndWait()
                    tts(content)
                else:
                    print("Maximum attempts reached.")
                    raise sr.WaitTimeoutError


PROMPT = "You are an useful assistant that helps me with my learning English."


def tts(text: str):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,

    )

    timestamp = datetime.now().isoformat()
    timestamp = re.sub(r'[^0-9]', '', timestamp)
    file_name = f"output{timestamp}.mp3"
    response.stream_to_file(file_name)
    # Load the MP3 file
    song = AudioSegment.from_mp3(file_name)
    # Export the song to WAV format
    tmp_file = f"temp{timestamp}.wav"
    song.export(tmp_file, format="wav")
    # Load the WAV file
    wave_obj = sa.WaveObject.from_wave_file(tmp_file)
    # Play the WAV file
    play_obj = wave_obj.play()
    # Wait until playback is finished
    play_obj.wait_done()


if __name__ == "__main__":
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an useful assistant that helps me with my learning English."},
            {"role": "user", "content": f"Make a greeting."}
        ]
    )
    content = response.choices[0].message.content
    tts(content)
    while True:
        try:
            transcription = recognize_speech_from_mic()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "assistant", "content": f"Hello, I am your assistant. How can I help you?"},
                    {"role": "user", "content": transcription.text}
                ]
            )
            content = response.choices[0].message.content
            tts(content)
        except sr.WaitTimeoutError:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a voice chatbot work as a professional and patient English learning "
                                        "assistant. You are waiting for a speech form user and it's long enough for a "
                                        "ending the conversation. Your task is to gently end the conversation."
                            }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "Hello, I am your assistant. How can I help you?"
                            }
                        ]
                    }])
            content = response.choices[0].message.content
            # engine.say(content)
            # engine.runAndWait()
            tts(content)
            break

