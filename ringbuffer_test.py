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
        self.start_pointer = 0
        self.end_pointer = 0
        self.read_start_pointer = 0

    def add_samples(self, samples):
        self.start_pointer = self.end_pointer
        self.end_pointer = (self.start_pointer + samples.shape[0]) % self.size
        self.read_start_pointer = 0

        # if the remaining space in buffer is bigger than samples, do this
        if self.start_pointer < self.end_pointer:
            self.data[self.start_pointer:self.start_pointer + samples.shape[0], :] = samples
            self.read_start_pointer = self.end_pointer


        # if samples will overflow remaining buffer space
        else:

            # this is the blank space left in the buffer
            space_left = self.size - self.start_pointer

            # if samples will fit in the buffer
            if samples.shape[0] < self.size:
                # this takes and fills the remaining space with as much of the samples array as will fit, starting with the top items

                self.data[self.start_pointer:, :] = samples[:space_left, :]

                # now fill the start of our buffer with the data from samples preceding the above
                samples_start_index = space_left

                self.data[0:samples.shape[0] - samples_start_index:] = samples[samples_start_index:]


    def __getitem__(self, indices):
        if isinstance(indices, slice):
            start = indices.start
            stop = indices.stop
            step = indices.step

            # handle [n:] and [:n]
            if start is None:
                start = 0
            if stop is None:
                stop = start
            if step is None:
                step = 1

            start += self.read_start_pointer
            start = start % self.size

            stop += self.read_start_pointer
            stop = stop % self.size

            if stop > start:
                return_value = self.data[start:stop:step, :]

            else:
                return_value = (np.concatenate((self.data[start:, :], self.data[:stop, :]))[::step, :])

            self.read_start_pointer = stop
            return return_value

            # todo this most recently retrieved thing still doesn't work all the way


buf = RingBuffer(10)
test = np.array([[1], [2], [3]])

buf.add_samples(test)
print(buf[:])
print(buf.data)
print("-------")
test = np.array([[4], [5], [6]])
buf.add_samples(test)
print("-------")
test = np.array([[7], [8], [9]])
buf.add_samples(test)
print(buf[:])
print(buf.data)
print("-------")
test = np.array([[10], [11], [12]])
buf.add_samples(test)
print(buf[:])
print(buf.data)
print("-------")

test = np.array([[13], [14], [15]])
buf.add_samples(test)

print("buf")
print(buf[:])
print("buf data")
#print(buf.data)
print("-------")

test = np.array([[16], [17], [18]])
buf.add_samples(test)

print("buf")
print(buf[:])
print("buf data")
print(buf.data)
print("-------")
