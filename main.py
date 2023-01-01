import os
import openai
import torch
import re
from krista_whisper import StreamHandler


from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import playsound
import dirtyjson

import json


print(torch.cuda.get_device_name(0))

openai.api_key = os.getenv("OPENAI_API_KEY")




from subprocess import call
import pyttsx3
import time, os, re
#import webbrowser #wip might use later

# My simple AI assistant using my LiveWhisper as a base. Can perform simple tasks such as:
# searching wikipedia, telling the date/time/weather/jokes, basic math and trivia, and more.
# ToDo: dictation to xed or similar, dynamically open requested sites/apps, or find simpler way.
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot

AIname = "Krista" # Name to call the assistant, such as "computer" or "jarvis". Activates further commands.
City = ''           # Default city for weather, Google uses + for spaces. (uses IP location if not specified)

# possibly redudant settings, but keeping them for easy debugging, for now.
Model = 'medium'     # Whisper model size (tiny, base, small, medium, large)
English = True      # Use english-only model?
Translate = False   # Translate non-english to english?
SampleRate = 44100  # Stream device recording frequency
BlockSize = 30      # Block size in milliseconds
Threshold = 0.05     # Minimum volume threshold to activate listening
Vocals = [50, 1000] # Frequency range to detect sounds that could be speech
EndBlocks = 40      # Number of blocks to wait before sending to Whisper

# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
session = Session(profile_name="krista")
polly = session.client("polly")


class Assistant:
  def __init__(self):
    self.running = True
    self.talking = False
    self.prompted = False
    self.espeak = pyttsx3.init()
    self.espeak.setProperty('rate', 180)  # speed of speech, 175 is terminal default, 200 is pyttsx3 default


  def analyze(self, input):  # This is the decision tree for the assistant
    string = "".join(ch for ch in input if ch not in ",.?!'").lower()  # Removes punctuations Whisper adds
    query = string.split()  # Split into words
    wake_words = ["hey krista", "hey christa", "hey christo", "hey chris"]

    if any(substring in string for substring in wake_words):  # if that's all they said, prompt for more input
      self.prompted = True
      playsound.playsound("acknowledge.mp3")
      self.speak("one moment!")
      f = open("openai_question_prompt_conditioning.json", "r")
      sample_responses = f.read()

      s = open("hamsats.json", "r")
      satlist = s.read()


      gpt_prompt = satlist + "is a list of valid satellites." + sample_responses + " is a list of sample responses.  make sure satellite is in the list of valid satellites, and set satellite to 'unknown' if it is not.  form the following question into properly formatted json as above:" + string + "{\n \"question\":"

      response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=gpt_prompt,
        temperature=0,
        max_tokens=256,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
      )


      request = "     {\"question\": " + response['choices'][0]['text']

      #print(request)
      request_data = dirtyjson.loads(request)

      #check first if response has satellite in it
      satellite_name = request_data['input_parameters']['satellite']
      print(request_data['input_parameters']['satellite'])

      gpt_prompt = "You are a chatbot. You know the following information: {'" + satellite_name + "_data':{'latitude': 38.9517, 'longitude': -92.3341', 'elevation': 'unknown', 'range': '500 km'}}.  You have been asked the following question: " + request + ".    Provide a friendly response that includes only the data asked for in the question.  Do not perform unit conversions if requested.  If the request requires information not found in output_parameters, don't include it in your response and apologize.   The response is: "

      response2 = openai.Completion.create(
        engine="text-davinci-003",
        prompt=gpt_prompt,
        temperature=0.7,
        max_tokens=256,
        top_p=.2,
        frequency_penalty=0.0,
        presence_penalty=0.0
      )

      response2 = response2['choices'][0]['text']
      print(response2)


      self.speak(response2)
      self.prompted = False

  def speak(self, text):
    #self.talking = True  # if I wanna add stop ability, I think function needs to be it's own object
    #print(f"\n\033[92m{text}\033[0m\n")
    #self.espeak.say(text)  # call(['espeak',text]) #'-v','en-us' #without pytttsx3
    #self.espeak.runAndWait()

    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Text="<speak><prosody rate=\"fast\">" + text + "</prosody></speak>", OutputFormat="mp3",
                                           VoiceId="Salli", Engine="neural", TextType="ssml")
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)

    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output = ".\speech.mp3"

            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())

                playsound.playsound(output)
                os.remove(output)
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)

    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)

    # Play the audio using the platform's default player



    self.talking = False






def main():
    try:
        Krista = Assistant() #voice object before this?
        handler = StreamHandler(Krista)
        handler.listen()
    except Exception as inst:
        print(inst)
    finally:
        print("\n\033[93mQuitting..\033[0m")
        #if os.path.exists('dictate.wav'): os.remove('dictate.wav')

if __name__ == '__main__':
    main()  # by Nik




