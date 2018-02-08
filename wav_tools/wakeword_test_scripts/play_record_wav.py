#!/usr/bin/env python
import argparse
import os
import platform
import pyaudio
import re
import struct
import signal
import subprocess
import sys
import time
import wave
from array import array
from datetime import datetime
import numpy as np

from utils.wav_handler import write_wav_file
from utils.xmos_subprocess import pstreekill, platform_is_windows

import threading
import Queue

# Run a command and pass through the stdout as soon as it arrives
# Note that most processes run with stdout buffered, so if it is a python process
# then use:
#   python -u <CMD>
# or any other command under Osx use:
#   script -q /dev/null <CMD>
class Runner():
  def __init__(self, cmd, regex, q=None):
    self.cmd = cmd
    self.proc = None
    self.regex = re.compile(regex)
    self.last_time = datetime.now()
    self.count = 0

    # A queue to communicate stdout to the audio thread
    if q is None:
      self.q = Queue.Queue()
    else:
      self.q = q

    self.stop_flag = False
    # Start a thread to run the command
    self.t = threading.Thread(target=self.process_manager)
    self.t.start()

  def stop(self):
    self.stop_flag = True
    self.t.join(timeout=0.5)
    if self.t.is_alive():
      print "Thread still alive: {}".format(' '.join(cmd))

    if self.proc is not None:
      pstreekill(self.proc)

  def execute_and_return_stdout(self, cmd):
    # Capture the stdout and stderr
    print "Running: '{}'".format(' '.join(cmd))
    self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    # for line in iter(self.proc.stdout.readline, b""):
    #     yield line
    while(True)
        output = self.proc.stdout.readline()
        if output == '' and proc.poll is not None:
            break
        if self.stop_flag:
            break
        if output:
            yield output
    print "Stopping Thread: {}".format(' '.join(cmd))
    self.proc.stdout.close()
    return_code = self.proc.wait()
    self.proc = None

  def process_manager(self):
    for line in self.execute_and_return_stdout(self.cmd):
        if self.regex.search(line):
            self.count += 1
            now = datetime.now()
            # Print just the seconds delta
            time_str = "{}: {}: ".format(
              datetime.time(now), str(now - self.last_time).split('.')[0])
            count_str = "({}): ".format(self.count)
            self.q.put(time_str + count_str + line.strip())
            self.last_time = now


# Playback index to be used by the playback callback
index = 0

# Handle the CTRL+C being pressed - set a global variable that will then stop
# the recording loop
ctrl_c_pressed = False
def signal_handler(signal, frame):
  global ctrl_c_pressed
  ctrl_c_pressed = True


def select_device(audio_manager, dev_name, dev_type):
    dev_count = audio_manager.get_device_count()

    dev_index = -1
    dev_found = False
    for i in range(dev_count):
        if dev_name in audio_manager.get_device_info_by_index(i)['name']:
            print "Selecting " + dev_type + " device:" + audio_manager.get_device_info_by_index(i)['name']
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


def play_and_record(pb_filename, pb_dev_name,
                    rec_dev_name, rec_sample_rate,
                    rec_sample_width, rec_channel_count,
                    queue):
    CHUNK_SIZE = 1024

    audio_manager = pyaudio.PyAudio()
    pb_dev_index, rec_dev_index = get_audio_devices(audio_manager, pb_dev_name, rec_dev_name)

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

    out_stream = audio_manager.open(format=audio_manager.get_format_from_width(
                                        wav_to_play.getsampwidth()),
                                    channels=wav_to_play.getnchannels(),
                                    rate=play_framerate,
                                    input=False, output=True,
                                    frames_per_buffer=CHUNK_SIZE,
                                    output_device_index=pb_dev_index,
                                    stream_callback=out_stream_callback)

    if rec_dev_name is None:
      out_stream.start_stream()
      while out_stream.is_active():
        if ctrl_c_pressed:
          break
        if queue.empty():
          time.sleep(0.1)
        else:
          trigger_line = queue.get()
          print trigger_line

    else:
      in_stream = audio_manager.open(format=audio_manager.get_format_from_width(rec_sample_width),
                                     channels=rec_channel_count,
                                     rate=rec_sample_rate,
                                     input=True, output=False,
                                     frames_per_buffer=CHUNK_SIZE,
                                     input_device_index=rec_dev_index)

      recorded_data = array('h')

      # The meta-data channel tracks when the audio triggered a keyword
      meta_data = array('h')

      # Round up to the closest integer number of input chunks to cover the duration of the playback
      chunks = int(((((n_frames * rec_sample_rate) / play_framerate) * repeat) + (CHUNK_SIZE - 1)) / CHUNK_SIZE)

      out_stream.start_stream()
      for i in range(chunks):
          # little endian, signed short
          data_chunk = array('h', in_stream.read(CHUNK_SIZE))

          # Manage the meta-data channel - whenever the other thread indicates
          # that the keyword has been triggered then annotate the audio channel
          keyword_triggered = False
          if not queue.empty():
            trigger_line = queue.get()
            print trigger_line
            keyword_triggered = True

          if keyword_triggered:
              meta_chunk = array('h', [0x7fff]*CHUNK_SIZE)
          else:
              meta_chunk = array('h', [0]*CHUNK_SIZE)

          if sys.byteorder == 'big':
              data_chunk.byteswap()

          recorded_data.extend(data_chunk)
          meta_data.extend(meta_chunk)

          if ctrl_c_pressed:
            break

    # Shutdown the output and input audio streams
    out_stream.stop_stream()
    out_stream.close()

    if rec_dev_name is not None:
      in_stream.stop_stream()
      in_stream.close()

    audio_manager.terminate()

    if rec_dev_name is None:
      return ([], [], 0)
    else:
      # Determine the number of seconds of audio per loop in case the recording
      # is going to be split
      track_seconds = n_frames / float(play_framerate)
      return (recorded_data, meta_data, track_seconds)


if __name__ == '__main__':
    global repeat

    argparser = argparse.ArgumentParser(description='XMOS synchronised WAV play/record script')
    argparser.add_argument('--monitor-command',
                           default=None,
                           help ='the command-line to run to monitor for ')
    argparser.add_argument('--monitor-regex',
                           default=None,
                           help ='when monitoring: the regular expression to detect a trigger')
    argparser.add_argument('--monitor-command-startup-seconds',
                           default=10,
                           type=int,
                           help ='number of seconds to allow the device to start')
    argparser.add_argument('playback_filename',
                           help='filename of the WAV to play',
                           metavar='playback-filename')
    argparser.add_argument('--playback-device-name',
                           default='Built-in Output',
                           help ='name of the playback device')
    argparser.add_argument('--recording-directory',
                           default='.',
                           help='directory where recorded file will be placed')
    argparser.add_argument('--recording-filename',
                           help='filename to use for the recorded WAV')
    argparser.add_argument('--recording-device-name',
                           default=None,
                           help ='name of the recording device')
    argparser.add_argument('--recording-sample-rate',
                           default=16000,
                           type=int,
                           help ='sample rate in Hz for recording device')
    argparser.add_argument('--recording-sample-width',
                           default=2,
                           type=int,
                           help ='sample width in bytes for recording device')
    argparser.add_argument('--recording-channel-count',
                           default=1,
                           type=int,
                           help ='number of channels to use on recording device')
    argparser.add_argument('--loop-count',
                           default=1,
                           type=int,
                           help ='number of times to repeat the output audio')
    argparser.add_argument('--split',
                           action='store_true',
                           help ='split the resulting output into a file per loop')
    argparser.add_argument('--annotate-wav',
                           action='store_true',
                           help ='add the triggering as an extra channel')

    args = argparser.parse_args()

    # Install the CTRL+C handler
    signal.signal(signal.SIGINT, signal_handler)

    # Set the global that is to be used by the audio callback
    repeat = args.loop_count

    # Only start the listener thread if there is a DUT
    if args.monitor_command is not None:
      runner = Runner(args.monitor_command.split(), args.monitor_regex)
      queue = runner.q
      time.sleep(args.monitor_command_startup_seconds)
    else:
      runners = None
      queue = Queue.Queue()

    ts = datetime.now().strftime('%Y%m%d_%H-%M-%S')

    # Setup default values which cannot be handled by argparser as required
    if args.recording_filename is None:
        args.recording_filename = 'recording_%s' % ts
    recording_path = os.path.join(args.recording_directory, args.recording_filename)

    # Play and record to the specified audio devices
    (recorded_data, meta_data, track_seconds) = play_and_record(
                                    args.playback_filename, args.playback_device_name,
                                    args.recording_device_name, args.recording_sample_rate,
                                    args.recording_sample_width, args.recording_channel_count,
                                    queue)

    if args.recording_device_name is not None:
      # If using a keyword firmware that has triggers and annotating wavs then
      # save the metadata as a second channel
      if args.monitor_command is not None and args.annotate_wav:
        n_channels = args.recording_channel_count + 1
        data = np.dstack((recorded_data, meta_data)).flatten()
      else:
        n_channels = args.recording_channel_count
        data = recorded_data

      if args.split:
        # Save the captured date into WAV files per loop
        n_frames = int(args.recording_sample_rate * track_seconds)
        for i in range(0, args.loop_count):
          file_data = data[i*n_frames*n_channels:(i+1)*n_frames*n_channels]
          write_wav_file(recording_path + '_{}'.format(i) + '.wav',
                         args.recording_sample_rate, n_channels, file_data)
      else:
        # Save the captured date in a single WAV file
        write_wav_file(recording_path + '.wav',
                       args.recording_sample_rate, n_channels, data)

    if runner is not None:
      print("{} Complete: {}".format(datetime.now().strftime('%Y%m%d_%H-%M-%S'),
                                     args.playback_filename))
      print runner.cmd, " Count: {}".format(runner.count)
      runner.stop()
