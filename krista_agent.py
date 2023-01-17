#
#     Copyright (C) 2019-present Nathan Odle
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the Server Side Public License, version 1,
#     as published by MongoDB, Inc.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     Server Side Public License for more details.
#
#     You should have received a copy of the Server Side Public License
#     along with this program. If not, email mysteriousham73@gmail.com
#
#     As a special exception, the copyright holders give permission to link the
#     code of portions of this program with the OpenSSL library under certain
#     conditions as described in each individual source file and distribute
#     linked combinations including the program with the OpenSSL library. You
#     must comply with the Server Side Public License in all respects for
#     all of the code used other than as permitted herein. If you modify file(s)
#     with this exception, you may extend this exception to your version of the
#     file(s), but you are not obligated to do so. If you do not wish to do so,
#     delete this exception statement from your version. If you delete this
#     exception statement from all source files in the program, then also delete
#     it in the license file.

import threading

import openai
import torch


from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import dirtyjson
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
import soundfile as sf
#
# print(torch.cuda.get_device_name(0))
# print("Agent")
openai.api_key = os.getenv("OPENAI_API_KEY")
from krista_util import IPCMessage

import os

session = Session(profile_name="krista")
polly = session.client("polly")


class KristaAgent:
    def __init__(self, state, transcription_queue, tui_queue_in, tui_queue_out):
        # print("Agent Init")
        self.state = state
        self.transcription_queue = transcription_queue
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out

        self.running = True

        self.process_messages()

        ipc_message = IPCMessage("AGENT_STATUS", "ready")
        self.tui_queue_in.put(ipc_message)

    def process_messages(self):

        ipc_message = IPCMessage("AGENT_STATUS", "ready")
        self.tui_queue_in.put(ipc_message)

        while True:
            while not self.transcription_queue.empty():
                ipc_message = self.transcription_queue.get()

                if ipc_message.type == "TRANSCRIPTION":
                    message = ipc_message.data
                    #print("from Krista: " + message)
                    self.state['agent_speaking'] = True
                    self.analyze(message)

    def playfile(self, filename):
        event = threading.Event()

        data, fs = sf.read(filename, always_2d=True)

        current_frame = 0

        def callback(outdata, frames, time, status):
            global current_frame
            # if status:

                #print(status)
            chunksize = min(len(data) - current_frame, frames)
            outdata[:chunksize] = data[current_frame:current_frame + chunksize]
            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
            current_frame += chunksize

        stream = sd.OutputStream(
            samplerate=fs, device=0, channels=data.shape[1],
            callback=callback, finished_callback=event.set)
        with stream:
            event.wait()  # Wait until playback is finished

    def analyze(self, input):



        self.prompted = True
        play(AudioSegment.from_mp3("acknowledge.mp3"))
        self.speak("one moment!")
        f = open("openai_question_prompt_conditioning.json", "r")
        sample_responses = f.read()
        f.close()

        s = open("hamsats.json", "r")
        satlist = s.read()
        s.close()

        gpt_prompt = satlist + "is a list of valid satellites." + sample_responses + " is a list of sample responses.  make sure satellite is in the list of valid satellites, and set satellite to 'unknown' if it is not.  form the following question into properly formatted json as above:" + input + "{\n \"question\":"

        ipc_message = IPCMessage("AGENT_STATUS", "thinking")
        self.tui_queue_in.put(ipc_message)

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

        ipc_message = IPCMessage("JSON_MESSAGE", request)
        self.tui_queue_in.put(ipc_message)

        ipc_message = IPCMessage("AGENT_STATUS", "ready")
        self.tui_queue_in.put(ipc_message)

        # print(request)
        request_data = dirtyjson.loads(request)

        # check first if response has satellite in it
        response2 = "I'm sorry, I didn't understand your question.  Please try again!"

        if 'input_parameters' in request_data:
            if 'satellite' in request_data['input_parameters']:

                satellite_name = request_data['input_parameters']['satellite']
                #print(request_data['input_parameters']['satellite'])

                gpt_prompt = "You are a chatbot. You know the following information: {'" + satellite_name + "_data':{'latitude': 38.9517, 'longitude': -92.3341', 'elevation': 'unknown', 'range': '500 km'}}.  You have been asked the following question: " + request + ".    Provide a friendly response that includes only the data asked for in the question.  Do not perform unit conversions if requested.  If the request requires information not found in output_parameters, don't include it in your response and apologize.   The response is: "

                ipc_message = IPCMessage("AGENT_STATUS", "thinking")
                self.tui_queue_in.put(ipc_message)

                response2 = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=gpt_prompt,
                    temperature=0.7,
                    max_tokens=256,
                    top_p=.2,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )

                response2 = response2['choices'][0]['text'].strip()

        ipc_message = IPCMessage("AGENT_STATUS", "ready")
        self.tui_queue_in.put(ipc_message)

        ipc_message = IPCMessage("AGENT_MESSAGE", response2)
        self.tui_queue_in.put(ipc_message)

        self.speak(response2)
        self.state['agent_prompted'] = False

    def speak(self, text):

        ipc_message = IPCMessage("AGENT_STATUS", "speaking")
        self.tui_queue_in.put(ipc_message)
        try:
            # Request speech synthesis
            response = polly.synthesize_speech(Text="<speak><prosody rate=\"fast\">" + text + "</prosody></speak>",
                                               OutputFormat="mp3",
                                               VoiceId="Salli", Engine="neural", TextType="ssml")
        except (BotoCoreError, ClientError) as error:
            # The service returned an error, exit gracefully
            print(error)
            sys.exit(-1)

        if "AudioStream" in response:

            with closing(response["AudioStream"]) as stream:
                output = ".\speech.mp3"

                try:

                    with open(output, "wb") as file:
                        file.write(stream.read())

                    self.state['agent_speaking'] = True

                    play(AudioSegment.from_mp3(output))
                    os.remove(output)

                    ipc_message = IPCMessage("AGENT_STATUS", "ready")
                    self.tui_queue_in.put(ipc_message)

                    self.state['agent_speaking'] = False


                except IOError as error:

                    print(error)
                    sys.exit(-1)

        else:

            sys.exit(-1)



