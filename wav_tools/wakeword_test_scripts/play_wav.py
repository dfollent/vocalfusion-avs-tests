#!/usr/bin/env python
import sys
import pyaudio
import time
import wave
import numpy
import struct


from play_record_wav import get_audio_devices



def play_wav(pb_filename, pb_dev_name):
    global index,repeat
    index = 0
    repeat = 1
    CHUNK_SIZE = 1024

    audio_manager = pyaudio.PyAudio()
    pb_dev_index, rec_dev_index = get_audio_devices(audio_manager, pb_dev_name, None)

    wav_to_play = wave.open(pb_filename, 'rb')
    samp_width = wav_to_play.getsampwidth()

    if samp_width == 2:
      struct_format_str = "<{}h"
    elif samp_width == 4:
      struct_format_str = "<{}i"
    else:
      print "ERROR: only support 16 or 32-bit audio"
      sys.exit(1)


    out_stream = audio_manager.open(format=audio_manager.get_format_from_width(samp_width),
                                    channels=wav_to_play.getnchannels(),
                                    rate=wav_to_play.getframerate(),
                                    output=True)

    data = wav_to_play.readframes(CHUNK_SIZE)

    while len(data) > 0:
        out_stream.write(data)
        data = wav_to_play.readframes(CHUNK_SIZE)




    out_stream.stop_stream()
    out_stream.close()
    audio_manager.terminate()
