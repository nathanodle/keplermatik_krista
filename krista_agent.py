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
from krista_util import IPCMessage

import threading

import openai

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import dirtyjson
from pydub import AudioSegment
from pydub.playback import play
import requests
import json
from thefuzz import fuzz

openai.api_key = os.getenv("OPENAI_API_KEY")

session = Session(profile_name="krista")
polly = session.client("polly")


class KristaAgent:
    def __init__(self, state, transcription_queue, tui_queue_in, tui_queue_out):

        self.satellite_list = {}
        self.state = state
        self.transcription_queue = transcription_queue
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out

        self.running = True

        ipc_message = IPCMessage("AGENT_STATUS", "ready")
        self.tui_queue_in.put(ipc_message)

        self.get_satellite_list()
        self.process_messages()

    def get_satellite_list(self):
        # api-endpoint
        URL = "http://192.168.1.2:8001/satellite_list"

        # sending get request and saving the response as response object
        r = requests.get(url=URL)

        # extracting data in json format
        json_data = json.loads(r.text)
        # print(json_data)
        self.satellite_list = json_data





    def get_closest_matches(self, input):

        fuzz_ratios = {}

        top_count = 100
        top_satellites = []
        for i in range(0, top_count - 1):
            top_satellites.append(("", 0))

        ipc_message = IPCMessage("JSON_MESSAGE", "")
        for satellite_name, norad_cat_id in self.satellite_list.items():
            fuzz_ratios[satellite_name] = fuzz.ratio(input, satellite_name)

        fuzz_ratios = dict(sorted(fuzz_ratios.items(), key=lambda x:x[1]))

        for satellite_name, score in fuzz_ratios.items():

            if score > top_satellites[0][1]:
                top_satellites.pop(0)
                top_satellites.append((satellite_name, score))

        top_satellites.append(('OSCAR 7', fuzz_ratios['OSCAR 7']))

        sat_list = list(map(lambda x: x[0], top_satellites))
        sat_list = json.dumps(sat_list)



        gpt_prompt = f"you are a state of the art text matching system.  {sat_list} is a list of satellite_names. which satellite name is the closest to {input}?  Respond with only the satellite name:"

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=gpt_prompt,
            temperature=0,
            max_tokens=3000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        closest_match = response['choices'][0]['text'].strip()

        ipc_message.data += "response: " + closest_match + "\n"
        ipc_message.data += f"{top_satellites}"

        #self.tui_queue_in.put(ipc_message)

        return closest_match




    def get_satellite_prediction(self, norad_cat_id):

        # api-endpoint
        URL = "http://192.168.1.2:8001/predict_now"

        # location given here
        observer_latitude = 38.951561
        observer_longitude = -92.328636

        prediction_request = '{"observer_latitude": ' + str(observer_latitude) + ', "observer_longitude": ' + str(observer_longitude) + ', "norad_cat_id": ' + str(norad_cat_id) + '}'

        r = requests.post(url=URL, data=prediction_request)

        # extracting data in json format
        prediction = r.text

        ipc_message = IPCMessage("PREDICTION_MESSAGE", str(prediction))
        #print(ipc_message.data)
        self.tui_queue_in.put(ipc_message)

        return prediction



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

    def analyze(self, input):
        self.state['agent_speaking'] = True
        play(AudioSegment.from_mp3("acknowledge.mp3"))
        self.speak("one moment!")
        f = open("openai_question_prompt_conditioning.json", "r")
        sample_responses = f.read()
        f.close()

        s = open("hamsats.json", "r")
        satlist = s.read()
        s.close()

        gpt_prompt = sample_responses + " is a list of sample responses.  form the following question into properly formatted json as above:" + input + "{\n \"question\":"

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


                input_satellite_name = request_data['input_parameters']['satellite']
                #satellite_name = request_data['input_parameters']['satellite']

                satellite_name = self.get_closest_matches(input_satellite_name)
                norad_cat_id = self.satellite_list[satellite_name.upper()]
                #print(satellite_name)
                #print(norad_cat_id)
                #print(request_data['input_parameters']['satellite'])
                prediction = self.get_satellite_prediction(norad_cat_id)
                #print(prediction)

                question = request_data['question']
                question = question.replace(input_satellite_name, satellite_name)
                request_data['input_parameters']['satellite'] = satellite_name
                request_data['question'] = question
                ipc_message = IPCMessage("JSON_MESSAGE", json.dumps(request_data))

                self.tui_queue_in.put(ipc_message)
                gpt_prompt = "You are a chatbot. You know the following information: {'" + satellite_name + "_data':" + prediction + ".  You have been asked the following question: " + json.dumps(request_data['question']) + ".    Provide a friendly response that includes only the data asked for in the question.  Do not perform unit conversions if requested.  If the request requires information not found in output_parameters, don't include it in your response and apologize.   The response is: "

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
        self.state['agent_speaking'] = False

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

                    # self.state['agent_speaking'] = True

                    play(AudioSegment.from_mp3(output))
                    os.remove(output)

                    ipc_message = IPCMessage("AGENT_STATUS", "ready")
                    self.tui_queue_in.put(ipc_message)

                    # self.state['agent_speaking'] = False


                except IOError as error:

                    print(error)
                    sys.exit(-1)

        else:

            sys.exit(-1)



