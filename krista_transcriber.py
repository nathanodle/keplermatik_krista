import collections

import playsound
import numpy as np
import os
import sounddevice as sd
import whisper
from scipy.io.wavfile import write

whisper_model_size = 'medium'

volume_activation_threshold = 0.01
sample_rate = 44100
block_size = 30
vocal_filter_range = [30, 10000]
max_silence_delay = 4


class RingBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = np.empty((capacity, 1369, 1))
        self.start = 0
        self.end = 0

    def is_empty(self):
        return self.start == self.end

    def clear(self):
        self.start = 0
        self.end = 0

    def append(self, item):
        self.data[self.end] = item
        self.end = (self.end + 1) % self.capacity
        if self.end == self.start:
            self.start = (self.start + 1) % self.capacity

    def __len__(self):
        if self.end >= self.start:
            return self.end - self.start
        else:
            return self.capacity - self.start + self.end

    def __getitem__(self, idx):
        if idx < 0:
            idx = len(self) + idx
        return self.data[(self.start + idx) % self.capacity]

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __concatenate__(self, other):
        return np.concatenate((self.data, other))


class Transcriber:
    def __init__(self, assistant):

        self.ring_buffer = RingBuffer(200)
        self.asst = assistant
        self.running = True
        self.silence_delay_counter = 0
        self.silence_during_speech_block = np.zeros((0, 1))
        self.buffer = np.zeros((0, 1))
        self.transcribe_now = False
        self.previous_buffer = np.zeros((0, 1))
        self.from_silence = True
        self.postroll_counter = 0
        self.recordings = 0
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(whisper_model_size + ".en")
        print("\033[90m Done.\033[0m")

    def process_audio(self, audio_sample_array, frames, time, status):

        if not self.asst.talking:
            audio_samples = audio_sample_array[:, ]

            if not any(audio_samples):
                print('\033[31m.\033[0m', end='', flush=True)  # if no input, prints red dots
                # print("\033[31mNo input or device is muted.\033[0m") #old way
                # self.running = False  # used to terminate if no input
                return

            fft = np.abs(np.fft.rfft(audio_samples))
            peak_frequency = np.argmax(fft) * sample_rate / frames

            rms = np.sqrt(np.mean(audio_samples ** 2))
            print("rms: " + str(rms) + "    peak frequency: " + str(peak_frequency))

            # If we hear speech, copy the previous block to the buffer
            if rms > volume_activation_threshold and not self.asst.talking:

                if self.from_silence is True:
                    print("about to cat")
                    self.buffer = np.concatenate((self.buffer, self.ring_buffer[0]), axis=0)

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
                    #self.ring_buffer.append(audio_sample_array)

                    if self.buffer.shape[0] > sample_rate:
                        # Haven't hit our silence limit, we're still recording
                        self.ring_buffer.append(audio_sample_array)

                        if self.silence_delay_counter > max_silence_delay:

                            print("go to transcribe")
                           # self.buffer = np.concatenate((self.buffer, self.previous_buffer.copy()))
                            write("dictate" + str(self.recordings) + ".wav", sample_rate, self.buffer)
                            self.transcribe_now = True
                            self.buffer = np.zeros((0, 1))
                            self.recordings += 1

                    self.silence_delay_counter += 1



    def transcribe(self):
        if self.transcribe_now:

            print("\n\033[90mTranscribing..\033[0m")
            result = self.model.transcribe("./dictate.wav", fp16=False, language='en', task='transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            if self.asst.analyze is not None:
                 self.asst.analyze(result['text'])

            self.transcribe_now = False

    def listen(self):
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")

        with sd.InputStream(channels=1, callback=self.process_audio, blocksize=1369, samplerate=sample_rate):
            while self.running and self.asst.running:
                self.transcribe()
