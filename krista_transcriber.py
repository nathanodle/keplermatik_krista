import collections

import playsound
import numpy as np

import os
import sounddevice as sd
import whisper
from scipy.io.wavfile import write

whisper_model_size = 'medium'

volume_activation_threshold = 0.1
sample_rate = 44100
block_size = 30
vocal_filter_range = [30, 10000]
max_silence_delay = 4


class RingBuffer:
    def __init__(self, size):
        self.size = size
        self.data = np.zeros((size, 1))
        self.curr_index = 0

    def add_samples(self, samples):

        # if the remaining space in buffer is bigger than samples, do this
        if samples.shape[0] + self.curr_index < self.size:
            self.data[self.curr_index:self.curr_index + samples.shape[0], :] = samples
            self.curr_index = self.curr_index + samples.shape[0]

        # if samples will overflow remaining buffer space
        else:
            # this is the blank space left in the buffer
            num_to_end = self.size - self.curr_index

            # if samples will fit in the buffer
            if samples.shape[0] < self.size:
                # this takes and fills the remaining space with as much of the samples array as will fit, starting with the top items
                self.data[self.curr_index:, :] = samples[:num_to_end, :]

                # now fill the start of our buffer with the data from samples preceding the above
                samples_start_index = num_to_end - self.curr_index
                self.data[0:self.curr_index - 1, :] = samples[samples_start_index:num_to_end - 1]


            # this is how much bigger than the remaining space the input is
            # num_wrapped = samples.shape[0] - num_to_end
            #
            #
            # # this takes and fills
            # self.data[:num_wrapped, :] = samples[num_to_end:, :]
            # self.curr_index = num_wrapped
        # else:
        #     self.data[self.curr_index:, :] = samples
        #     self.curr_index += samples.shape[0]

    def __getitem__(self, indices):
        if isinstance(indices, slice):
            start = indices.start
            stop = indices.stop
            step = indices.step
            if start is None:
                start = 0
            if stop is None:
                stop = self.size
            if step is None:
                step = 1
            if start < 0:
                start += self.size
            if stop < 0:
                stop += self.size
            if start >= self.size:
                start -= self.size
            if stop >= self.size:
                stop -= self.size
            if start < self.curr_index:
                if stop <= self.curr_index:
                    return self.data[start:stop:step, :]
                else:
                    return np.concatenate((self.data[start:, :], self.data[:stop, :]))[::step, :]
            else:
                return self.data[start:stop:step, :]
        else:
            if indices < 0:
                indices += self.size
            if indices >= self.size:
                indices -= self.size
            if indices < self.curr_index:
                return self.data[indices, :]
            else:
                return self.data[indices - self.size, :]


class Transcriber:
    def __init__(self, assistant):

        self.ring_buffer = RingBuffer(2000)
        self.asst = assistant
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
            # print("rms: " + str(rms) + "    peak frequency: " + str(peak_frequency))

            # If we hear speech, copy the previous block to the buffer
            if rms > volume_activation_threshold and not self.asst.talking:

                if self.from_silence is True:
                    print("adding " + str(self.preroll_count) + " preroll frames")
                    print("buffer_data")
                    #print(self.buffer)
                    print("-------")
                    print("ring_buffer data")
                    print(self.ring_buffer.data)
                    print("-------")
                    self.buffer = np.concatenate((self.buffer, self.ring_buffer[1:]))
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
                        # Haven't hit our silence limit, we're still recording
                        self.ring_buffer.add_samples(audio_sample_array)

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