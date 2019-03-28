#!/usr/bin/env python
import sys
import pyaudio
import wave
import struct
import numpy as np
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



def play_wav(pb_filename, pb_dev_name, channel=0):
    CHUNK_SIZE = 1024

    audio_manager = pyaudio.PyAudio()
    pb_dev_index, rec_dev_index = get_audio_devices(audio_manager, pb_dev_name, None)


    wav_to_play = wave.open(pb_filename, 'rb')
    samp_width = wav_to_play.getsampwidth()
    wav_channels = wav_to_play.getnchannels()

    if samp_width == 2:
      struct_format_str = "<{}h"
    elif samp_width == 4:
      struct_format_str = "<{}i"
    else:
      raise Exception("ERROR: only support 16 or 32-bit audio")
      # sys.exit(1)


    out_stream = audio_manager.open(format=audio_manager.get_format_from_width(samp_width),
                                    channels=wav_to_play.getnchannels(),
                                    rate=wav_to_play.getframerate(),
                                    output=True,
                                    output_device_index=pb_dev_index)

    data = wav_to_play.readframes(CHUNK_SIZE)

    if wav_channels == 1:
        while len(data) > 0:
            stereo_signal = np.zeros([len(data), 2]).tostring()
            stereo_signal[:, channel] = data[:]
            out_stream.write(stereo_signal)
            data = wav_to_play.readframes(CHUNK_SIZE)
    else:
        while len(data) > 0:
            out_stream.write(data)
            data = wav_to_play.readframes(CHUNK_SIZE)


    out_stream.stop_stream()
    out_stream.close()
    audio_manager.terminate()


def get_gained_frames(wav_file, gain):
    CHUNK_SIZE = 1024    
    frame = wav_file.readframes(CHUNK_SIZE)
    
    if len(frame) > 0:    
        decoded = np.fromstring(frame, 'Int32')
        gained_decoded = (10**(float(gain) / 20.0)) * decoded
        # frame = gained_decoded.tostring()
        return gained_decoded

    return frame



def play_gained_wav(filename, pb_dev_name, gain, channel=0):

    audio_manager = pyaudio.PyAudio()
    pb_dev_index, rec_dev_index = get_audio_devices(audio_manager, pb_dev_name, None)

    wav_to_play = wave.open(filename, 'rb')
    samp_width = wav_to_play.getsampwidth()
    wav_channels = wav_to_play.getnchannels()
    framecount = wav_to_play.getnframes()

    # print "Width: {}".format(samp_width)
    # print "Channels: {}".format(wav_channels)
    # print "Count: {}".format(framecount)

    if samp_width != 2 and samp_width != 4:
        raise Exception("Must be 16 or 32-bit audio")

    if wav_channels != 1:
        raise Exception("Must be single channel audio")


    encoded_data = wav_to_play.readframes(framecount)

    # if samp_width == 3:
    #     # Convert to 32 bit data
    #     temp = bytearray()
    #     for i in range(0, len(encoded_data), 3):
    #         temp.append(0)
    #         temp.extend(encoded_data[i:i+3])

    #     encoded_data = temp
    #     samp_width = 4


    dtype = '<i{}'.format(samp_width)

    decoded_data = np.frombuffer(encoded_data, dtype=dtype)
    gained_decoded_data = (10**(float(gain) / 20.0)) * decoded_data

    # print "{} {}, dtype={}".format(gained_decoded_data[0], gained_decoded_data[-1], dtype)

    stereo_data = np.zeros([2*len(gained_decoded_data), 1])
    for i, sample in enumerate(gained_decoded_data):
        stereo_data[2*i + channel] = sample


    gained_encoded_data = stereo_data.astype(dtype).tostring()


    out_stream = audio_manager.open(format=audio_manager.get_format_from_width(samp_width),
                                    channels=2,
                                    rate=wav_to_play.getframerate(),
                                    output=True,
                                    output_device_index=pb_dev_index)

    out_stream.write(gained_encoded_data)


    out_stream.stop_stream()
    out_stream.close()
    audio_manager.terminate()
