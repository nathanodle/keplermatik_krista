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
        self.buffer_wrapped = False
        self.read_pointer_overtake = True


    def add_samples(self, samples):

        samples_length = samples.shape[0]
        start_write_pointer = self.write_pointer
        # if the remaining space in buffer is bigger than samples, do this
        if samples_length + self.write_pointer < self.size:

            self.data[self.write_pointer:self.write_pointer + samples.shape[0], :] = samples
            self.write_pointer = self.write_pointer + samples_length

            # todo:  the issue is in here somewhere.  Basically, we're not detecting all conditions where write_pointer overtakes read_pointer
            print(" start_write_pointer: " + str(start_write_pointer))
            print(" read_pointer: " + str(self.read_pointer))
            print(" write_pointer: " + str(self.write_pointer))
            print(" read_pointer_overtake: " + str(self.read_pointer_overtake))
            if self.buffer_wrapped:
                if self.read_pointer_overtake:
                    if self.read_pointer > self.write_pointer - 1:
                        self.read_pointer = self.write_pointer
                        self.read_pointer_overtake = True

                    print("set read pointer from straight write (overflow) to " + str(self.read_pointer))



            print("no buffer wrap")

        # if samples will overflow remaining buffer space
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
            print("** " + str(self.read_pointer) + " " + str(self.write_pointer))

            # if self.read_pointer_overtake:
            #     self.read_pointer_overtake = True
            #     self.read_pointer = self.write_pointer
            #todo:  the issue is in here somewhere.  Basically, we're not detecting all conditions where write_pointer overtakes read_pointer
            print(" start_write_pointer: " + str(start_write_pointer))
            print(" read_pointer: " + str(self.read_pointer))
            print(" write_pointer: " + str(self.write_pointer))
            print(" read_pointer_overtake: " + str(self.read_pointer_overtake))
            if self.read_pointer < start_write_pointer and self.read_pointer > self.write_pointer - 1:
                if self.read_pointer_overtake:
                    self.read_pointer = self.write_pointer
                    print("set read pointer from overflow write (read < write) to " + str(self.read_pointer))
                print("set overtake (read <= start_write, read > write - 1)")
                self.read_pointer_overtake = True

            if self.read_pointer <= start_write_pointer and self.read_pointer < self.write_pointer - 1:
                if self.read_pointer_overtake:
                    self.read_pointer = self.write_pointer
                    print("set read pointer from overflow write (read < write) to " + str(self.read_pointer))
                print("set overtake (read <= start_write, read < write - 1)")
                self.read_pointer_overtake = True


        print("leaving read pointer: " + str(self.read_pointer) + " write pointer: " + str(self.write_pointer))

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

            # if self.read_pointer < self.write_pointer:
            #     print(" using read_pointer")
            start += self.read_pointer
            # else:
            #     print(" using read_finish_pointer")
            #     start += self.read_finish_pointer

            start = start % self.size

            stop += self.write_pointer
            stop = stop % self.size

            print(" " + str(self.read_pointer) + " " + str(self.write_pointer))
            print(" " + str(start) + " " + str(stop))

            if stop > start:
                return_value = self.data[start:stop:step, :]

            else:
                return_value = np.concatenate((self.data[start:, :], self.data[:stop, :]))[::step, :]

            self.read_pointer = stop % self.size
            self.read_finish_pointer = stop % self.size

            print("set read pointer from read to " + str(self.read_pointer))

            self.read_pointer_overtake = False
            self.buffer_wrapped = False

            return return_value

            # todo this most recently retrieved thing still doesn't work all the way


buf = RingBuffer(10)
test = np.array([[-2], [-1], [0]])

for i in range(0, 8):

    test = test + 3
    buf.add_samples(test)

    print(str(i) + " --------")
    print(" " + str(buf.data.flatten()))
    if i not in range(3,4):
        print(" " + str(buf[:].flatten()))
    print("  -------")
    print("")

# buf.add_samples(test)
# print(buf[:])
# print(buf.data)
# print("-------")
# test = np.array([[4], [5], [6]])
# buf.add_samples(test)
# print("-------")
# test = np.array([[7], [8], [9]])
# buf.add_samples(test)
# print(buf[:])
# print(buf.data)
# print("-------")
# test = np.array([[10], [11], [12]])
# buf.add_samples(test)
# print(buf[:])
# print(buf.data)
# print("-------")
#
# test = np.array([[13], [14], [15]])
# buf.add_samples(test)
#
# print("buf")
# print(buf[:])
# print("buf data")
# #print(buf.data)
# print("-------")
#
# test = np.array([[16], [17], [18]])
# buf.add_samples(test)
#
# print("buf")
# print(buf[:])
# print("buf data")
# print(buf.data)
# print("-------")
