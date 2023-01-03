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
