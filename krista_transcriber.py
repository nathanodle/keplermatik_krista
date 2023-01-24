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
import requests
# import whisper
from krista_util import IPCMessage

whisper_model_size = 'medium'


class Transcriber:
    def __init__(self, state, recording_queue, transcription_queue, tui_queue_in, tui_queue_out):

        #print("Transcriber Init")
        self.state = state
        self.recording_queue = recording_queue
        self.transcription_queue = transcription_queue
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out

        ipc_message = IPCMessage("TRANSCRIBER_STATUS", "not_ready")
        self.tui_queue_in.put(ipc_message)

        #self.model = whisper.load_model(whisper_model_size + ".en")

        ipc_message = IPCMessage("TRANSCRIBER_STATUS", "ready")
        self.tui_queue_in.put(ipc_message)

        self.transcribe()

    def get_transcription(self, filename):
        url = 'http://192.168.1.2:8002/transcribe'
        with open(filename, 'rb') as file:

            file = {'file': file}
            resp = requests.post(url=url, files=file)
            transcription = resp.json()["transcription_result"]["text"]

        return transcription

    def transcribe(self):
        while True:

            while not self.recording_queue.empty():
                ipc_message = self.recording_queue.get()

                if ipc_message.type == "RECORDING":
                    filename = ipc_message.data
                    #print("transcribing")

                    ipc_message = IPCMessage("TRANSCRIBER_STATUS", "transcribing")
                    self.tui_queue_in.put(ipc_message)

                    #result = self.model.transcribe(filename, fp16=False, language='en', task='transcribe')
                    result = self.get_transcription(filename)

                    ipc_message = IPCMessage("TRANSCRIBER_STATUS", "ready")
                    self.tui_queue_in.put(ipc_message)

                    message = "".join(ch for ch in result if ch not in ",.?!'").lower()
                    ipc_message = IPCMessage("RAW_TRANSCRIPTION", message)
                    self.tui_queue_in.put(ipc_message)
                    wake_words = ["hey krista", "hey christa", "hey christo", "hey chris"]

                    message = message.replace("christa", "krista")
                    message = message.replace("christo", "krista")
                    message = message.replace("chris", "krista")

                    self.state['agent_prompted'] = True

                    if any(substring in message for substring in wake_words):

                        # print(message)
                        ipc_message = IPCMessage("TRANSCRIPTION", message)
                        self.transcription_queue.put(ipc_message)
                        self.tui_queue_in.put(ipc_message)




