#!/usr/bin/env python
import sys
import pyaudio
import wave
import struct


def select_device(audio_manager, dev_name, dev_type):
    dev_count = audio_manager.get_device_count()

    dev_index = -1
    dev_found = False
    for i in range(dev_count):
        if dev_name in audio_manager.get_device_info_by_index(i)['name']:
            # print "Selecting " + dev_type + " device:" + audio_manager.get_device_info_by_index(i)['name']
            dev_index = i
            dev_found = True
            break

    if dev_found == False:
      print "ERROR: {} device not found".format(dev_type)
      print "  Available devices are:"
      for i in range(dev_count):
        print "    {}".format(audio_manager.get_device_info_by_index(i)['name'])
      sys.exit(1)

    return dev_index

def get_audio_devices(audio_manager, pb_dev_name, rec_dev_name):
    pb_dev_index = select_device(audio_manager, pb_dev_name, 'Playback')
    if rec_dev_name is None:
      rec_dev_index = -1
    else:
      rec_dev_index = select_device(audio_manager, rec_dev_name, 'Recording')

    return (pb_dev_index, rec_dev_index)



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
