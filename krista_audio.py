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


import numpy
import numpy as np
from scipy._lib._ccallback import CData

from ringbuffer import RingBuffer
import sounddevice as sd
import whisper
from scipy.io.wavfile import write
from krista_util import IPCMessage

whisper_model_size = 'medium'

volume_activation_threshold = 0.1
sample_rate = 16000
write_sample_rate = 16000
block_size = 30
vocal_filter_range = [30, 10000]
max_silence_delay = 5


class Recorder:
    def __init__(self, state, recording_queue, tui_queue_in, tui_queue_out):
        print("Recorder Init")
        self.state = state
        self.recording_queue = recording_queue
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out

        self.ring_buffer = RingBuffer(2000)

        self.running = True
        self.silence_delay_counter = 0
        self.silence_during_speech_block = np.zeros((0, 1))
        self.buffer = np.zeros((0, 1))
        self.transcribe_now = False
        self.previous_buffer = np.zeros((0, 1))
        self.from_silence = False
        self.preroll_count = 5
        self.postroll_counter = 0
        self.recordings = 0

        self.listen()

    def process_audio(self, audio_sample_array: numpy.ndarray, frames: int, time: CData, status: sd.CallbackFlags):

        if not self.state['agent_speaking']:
            audio_samples = audio_sample_array[:, ]

            if not any(audio_samples):
                print(".")

                return

            fft = np.abs(np.fft.rfft(audio_samples))
            peak_frequency = np.argmax(fft) * sample_rate / frames

            rms = np.sqrt(np.mean(audio_samples ** 2))

            if rms > volume_activation_threshold:

                if self.from_silence is True:
                    print("adding " + str(self.preroll_count) + " preroll frames")
                    print("buffer_data")
                    #print(self.buffer)
                    print("-------")
                    print("ring_buffer data")
                    print(self.ring_buffer.data)
                    print("-------")
                    #self.buffer = np.concatenate((self.buffer, self.ring_buffer[1:]))
                    print("buffer_data")
                    #print(self.buffer)
                    print("-------")
                    print('\033[31m.\033[0m', end='', flush=True)

                print('.', end='', flush=True)
                self.buffer = np.concatenate((self.buffer, audio_sample_array))
                self.silence_delay_counter = 0
                self.from_silence = False

            else:
                if self.postroll_counter < 1:
                    self.buffer = np.concatenate((self.buffer, audio_sample_array))
                    self.postroll_counter += 1

                else:
                    self.postroll_counter = 0
                    self.from_silence = True
                    # self.ring_buffer.append(audio_sample_array)

                    if self.buffer.shape[0] > sample_rate:

                        #self.ring_buffer.add_samples(audio_sample_array)

                        if self.silence_delay_counter > max_silence_delay:
                            #print("go to transcribe")

                            filename = "dictate.wav"
                            write(filename, write_sample_rate, self.buffer)

                            self.buffer = np.zeros((0, 1))
                            self.recordings += 1

                            ipc_message = IPCMessage("RECORDING", filename)
                            self.recording_queue.put(ipc_message)

                    self.silence_delay_counter += 1



    def listen(self):
        print("listening")
        sd.default.device = 0

        with sd.InputStream(channels=1, callback=self.process_audio, blocksize=1369, samplerate=sample_rate):
            while True:
                pass
