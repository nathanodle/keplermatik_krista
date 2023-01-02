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