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

from multiprocessing import set_start_method


from krista_transcriber import Transcriber
from krista_agent import KristaAgent
from krista_audio import Recorder
from krista_tui import KristaTUI
import multiprocessing as mp

def transcription_process(state, recording_queue, transcription_queue, tui_queue_in, tui_queue_out):

    transcriber = Transcriber(state, recording_queue, transcription_queue, tui_queue_in, tui_queue_out)

def agent_process(state, transcription_queue, tui_queue_in, tui_queue_out):

    agent = KristaAgent(state, transcription_queue, tui_queue_in, tui_queue_out)

def audio_process(state, recording_queue, tui_queue_in, tui_queue_out):

    audio = Recorder(state, recording_queue, tui_queue_in, tui_queue_out)

def tui_process(state, tui_queue_in, tui_queue_out):

    tui = KristaTUI(state, tui_queue_in, tui_queue_out)


if __name__ == '__main__':
    set_start_method("spawn")

    state_manager = mp.Manager()
    state = state_manager.dict()

    state['agent_speaking'] = False
    state['agent_prompted'] = False

    transcription_queue = mp.Queue()
    recording_queue = mp.Queue()
    tui_queue_in = mp.Queue()
    tui_queue_out = mp.Queue()

    agent_p = mp.Process(target=agent_process, args=(state, transcription_queue, tui_queue_in, tui_queue_out))
    transcription_p = mp.Process(target=transcription_process, args=(state, recording_queue, transcription_queue, tui_queue_in, tui_queue_out))
    audio_p = mp.Process(target=audio_process, args=(state, recording_queue, tui_queue_in, tui_queue_out))
    # tui_p = mp.Process(target=tui_process, args=(state, tui_queue_in, tui_queue_out))

    agent_p.start()
    transcription_p.start()
    audio_p.start()
    # tui_p.start()


    # tui_p.join()

    tui = KristaTUI(state, tui_queue_in, tui_queue_out)

    agent_p.join()
    transcription_p.join()
    audio_p.join()

