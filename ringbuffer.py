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

import numpy as np


class RingBuffer:
    def __init__(self, size):
        self.size = size
        self.data = np.zeros((size, 1))
        self.read_pointer = 0
        self.write_pointer = 0
        self.read_finish_pointer = 0
        self.empty = True
        self.buffer_wrapped = False
        self.read_pointer_lapped = False

    @property
    def length(self):
        if self.read_pointer_lapped:
            length = self.size

        elif self.write_pointer == self.read_pointer:
            length = 0

        elif self.write_pointer > self.read_pointer:
            length = self.write_pointer - self.read_pointer

        else:
            length = self.size - self.read_pointer + self.write_pointer

        return length

    def add_samples(self, samples):
        overtake = False
        samples_length = samples.shape[0]
        start_write_pointer = self.write_pointer

        # if the remaining space in buffer is bigger than samples, do this
        if samples_length + self.write_pointer < self.size:

            self.data[self.write_pointer:self.write_pointer + samples.shape[0], :] = samples
            self.write_pointer = self.write_pointer + samples_length

            if self.buffer_wrapped and start_write_pointer <= self.read_pointer <= self.write_pointer:
                overtake = True

        else:

            self.buffer_wrapped = True

            start_write_pointer = self.write_pointer
            # this is the space left between the write pointer and the end of the array
            space_left = self.size - self.write_pointer

            # this takes and fills the remaining space with as much of the samples array as will fit, starting with the top items
            self.data[self.write_pointer:, :] = samples[:space_left, :]

            # now fill the start of our buffer with the data from samples preceding the above
            samples_start_index = space_left

            self.write_pointer = samples.shape[0] - samples_start_index
            self.data[0:self.write_pointer:] = samples[samples_start_index:]

            if self.read_pointer < start_write_pointer and self.read_pointer + self.size < start_write_pointer + samples.shape[0]:
                overtake = True

            if start_write_pointer < self.read_pointer < start_write_pointer + samples.shape[0]:
                overtake = True

        if overtake or self.read_pointer_lapped:
            self.read_pointer = self.write_pointer
            self.read_pointer_lapped = True

        self.empty = False

    def __len__(self):

        return self.length

    def __getitem__(self, indices):

        return_value = 0

        if not self.empty:

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

                start += self.read_pointer

                start = start % self.size

                stop += self.write_pointer
                stop = stop % self.size

                if stop > start:
                    return_value = self.data[start:stop:step, :]

                else:
                    return_value = np.concatenate((self.data[start:, :], self.data[:stop, :]))[::step, :]

                self.read_pointer = stop % self.size
                self.read_finish_pointer = stop % self.size

                self.empty = True
                self.read_pointer_lapped = False
                self.buffer_wrapped = False

        return return_value



