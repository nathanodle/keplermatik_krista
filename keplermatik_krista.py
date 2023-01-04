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

import os
import traceback

import openai
import torch
import re
from krista_transcriber import transcriber

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import playsound
import dirtyjson

if __name__ == '__main__':
    transcription_queue = multiprocessing.Queue()

    transcription_p = multiprocessing.Process(target=transcription_process, args=(transcription_queue,))
    main_p = multiprocessing.Process(target=main_process, args=(transcription_queue,))

    transcription_p.start()
    main_p.start()

    transcription_p.join()
    main_p.join()
