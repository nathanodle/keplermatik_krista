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

import whisper
from krista_util import IPCMessage

whisper_model_size = 'medium'


class Transcriber:
    def __init__(self, state, recording_queue, transcription_queue, tui_queue_in, tui_queue_out):

        print("Transcriber Init")
        self.state = state
        self.recording_queue = recording_queue
        self.transcription_queue = transcription_queue
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out

        print("loading model")
        self.model = whisper.load_model(whisper_model_size + ".en")
        print("done")

        self.transcribe()


    def transcribe(self):
        while True:

            while not self.recording_queue.empty():
                ipc_message = self.recording_queue.get()

                if ipc_message.type == "RECORDING":
                    filename = ipc_message.data
                    #print("transcribing")
                    result = self.model.transcribe(filename, fp16=False, language='en', task='transcribe')

                    message = "".join(ch for ch in result['text'] if ch not in ",.?!'").lower()
                    print(message)
                    wake_words = ["hey krista", "hey christa", "hey christo", "hey chris"]

                    self.state['agent_prompted'] = True

                    if any(substring in message for substring in wake_words):
                        print(message)
                        ipc_message = IPCMessage("TRANSCRIPTION", message)
                        self.transcription_queue.put(ipc_message)



