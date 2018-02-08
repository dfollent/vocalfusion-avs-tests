#!/usr/bin/env python
import sys
import pyaudio
import time
import wave


from play_record_wav import get_audio_devices

def out_stream_callback(in_data, frame_count, time_info, status):
    global index, repeat

    n_samples = frame_count*n_channels

    npdata = samples[index:index+n_samples]
    data = npdata.tolist()

    outstanding = n_samples - len(data)
    if outstanding > 0:
      # Running off the end of the audio
      repeat -= 1
      if repeat > 0:
        npdata = samples[0:outstanding]
        data += npdata.tolist()
        index = outstanding
    else:
      index = index + n_samples

    data = struct.pack(struct_format_str.format(len(data)), *data)
    return (data, pyaudio.paContinue)


def play_wav(pb_filename, pb_dev_name):
    CHUNK_SIZE = 1024
    audio_manager = pyaudio.PyAudio()
    pb_dev_index, rec_dev_index = get_audio_devices(audio_manager, pb_dev_name, NULL)

    wav_to_play = wave.open(pb_filename, 'rb')
    samp_width = wav_to_play.getsampwidth()

    if samp_width == 2:
      struct_format_str = "<{}h"
    elif samp_width == 4:
      struct_format_str = "<{}i"
    else:
      print "ERROR: only support 16 or 32-bit audio"
      sys.exit(1)

    n_frames = wav_to_play.getnframes()
    n_channels = wav_to_play.getnchannels()
    play_framerate = wav_to_play.getframerate()
    data = wav_to_play.readframes(n_frames)
    samples = np.array(struct.unpack(struct_format_str.format(n_frames*n_channels), data))

    out_stream = audio_manager.open(format=audio_manager.get_format_from_width(
                                        wav_to_play.getsampwidth()),
                                    channels=wav_to_play.getnchannels(),
                                    rate=play_framerate,
                                    input=False, output=True,
                                    frames_per_buffer=CHUNK_SIZE,
                                    output_device_index=pb_dev_index,
                                    stream_callback=out_stream_callback)

    # Wait for file to finish or Ctrl+C to be pressed
    try:
        out_stream.start_stream()
        while out_stream.is_active():
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    out_stream.stop_stream()
    out_stream.close()
    audio_manager.terminate()
