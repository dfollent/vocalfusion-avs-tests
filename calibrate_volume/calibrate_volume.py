#!/usr/bin/env python2
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import log_utils
import signal
import subprocess
import argparse
import threading
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import spline
import pyaudio
import wave


MAX_VOLUME = 100
ERROR_MARGIN = 0.25
REQ_STABILITY = 15

dB_weights = ["dBA", "dBC", "dBZ"]


class spl_meter():
    def __init__(self, cmd, weight):
        self.value = 0.0
        self.cmd = cmd
        self.thread = threading.Thread(target=self.run)
        self._stop_event = threading.Event()
        self.running = False
        self.weight_index = dB_weights.index(weight) if weight in dB_weights else 0

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.thread.join(timeout=2)

    def run(self):
        process = subprocess.Popen(self.cmd.split(), env=os.environ.copy(),
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while(True):
            line = process.stdout.readline()
            if line != '':
                self.running = True
                new_val = float(line.split(',')[self.weight_index])
                self.value = (3*self.value + new_val) / 4
            else:
                break

            if self._stop_event.is_set():
                break

        os.kill(process.pid, signal.SIGINT)

    def get_value(self):
        return self.value

    def __del__(self):
        self._stop_event.set()

def control_algo(y, yc, h=1, Kp=1, Ti=1, u0=0, e0=0):
	"""Calculate System Input using a PI Controller

	Arguments:
	y  .. Measured Output of the System
	yc .. Desired Output of the System
	h  .. Sampling Time
	Kp .. Controller Gain Constant
	Ti .. Controller Integration Constant
	u0 .. Initial state of the integrator
	e0 .. Initial error

	Make sure this function gets called every h seconds!
	"""
	# Step variable
	k = 0
	# Initialization
	ui_prev = u0
	e_prev = e0

	while 1:
		# Error between the desired and actual output
		e = yc - y
		# Integration Input
		ui = ui_prev + 1.0/Ti * h*e
		# Adjust previous values
		e_prev = e
		ui_prev = ui
		# Calculate input for the system
		u = Kp * (e + ui )
		k += 1
		yield u

# Returns int in range 0 - 100
def get_volume():
    cmd = ["osascript", "-e", "output volume of (get volume settings)"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    line = process.stdout.readline()
    return float(line)

# Set volume in range 0 - 100
def set_volume(volume):
    volume = min(round(volume), MAX_VOLUME)
    subprocess.call(["osascript", "-e", "set volume output volume {}".format(volume)])

def select_device(audio_manager, dev_name, dev_type):
    dev_count = audio_manager.get_device_count()

    dev_index = -1
    dev_found = False
    for i in range(dev_count):
        if dev_name in audio_manager.get_device_info_by_index(i)['name']:
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

def get_audio_stream(pb_file, pb_device):
    audio_out = pyaudio.PyAudio()
    wav_to_play = wave.open(pb_file, 'rb')

    audio_out_index = None
    if pb_device is not None:
        audio_out_index = select_device(audio_out, pb_device, 'Output')


    def callback(in_data, frame_count, time_info, status):
        data = wav_to_play.readframes(frame_count)
        return (data, pyaudio.paContinue)

    stream = audio_out.open(format=audio_out.get_format_from_width(wav_to_play.getsampwidth()),
                            channels=wav_to_play.getnchannels(),
                            rate=wav_to_play.getframerate(),
                            output=True,
                            stream_callback=callback,
                            output_device_index=audio_out_index)
    return wav_to_play, stream

def plot(time_list, feedback_list, volume_list):
    time_sm = np.array(time_list)
    plt.plot(time_list, feedback_list, label='Feedback (dB)')
    plt.plot(time_list, volume_list, label='Volume')
    plt.legend()
    plt.ylim((min(min(feedback_list), min(volume_list))-1, max(max(feedback_list), max(volume_list))+1))
    plt.xlabel('Ticks (0.25s)')
    plt.ylabel('Levels')
    plt.title('SPL Calibration')
    plt.grid(True)
    plt.show()

def run(spl_cmd, setpoint, weight, pb_file, pb_device=None, make_plot=False):
    spl = spl_meter(spl_cmd, weight)
    spl.start()
    time.sleep(5)
    if spl.running == False:
        spl.stop()
        raise Exception('SPL meter is not running. Cannot proceed.')

    wav_to_play, stream = get_audio_stream(pb_file, pb_device)
    stream.start_stream()
    time.sleep(3)

    feedback_list = []
    time_list = []
    volume_list = []

    try:
        volume = get_volume()
        error = 0
        output = 0
        stability_count = 0
        feedback = 0
        time_step = 1
        while stream.is_active():
            feedback = spl.get_value()
            error = setpoint - feedback

            input_generator = control_algo(feedback, setpoint, h=0.3, Kp=0.2, Ti=3.5, e0=error)
            output = next(input_generator)

            if abs(error) <= ERROR_MARGIN and abs(output) <= ERROR_MARGIN:
                stability_count += 1
                if stability_count >= REQ_STABILITY:
                    break
            else:
                stability_count = 0

            volume = volume + output
            adj_volume = min(100, max(0, round(volume)))
            set_volume(adj_volume)

            feedback_list.append(feedback)
            time_list.append(time_step)
            volume_list.append(adj_volume)
            time.sleep(0.25 - (time.time() % 0.25)) # Guarantee loop period of 0.25s
            time_step += 1

        if abs(error) > ERROR_MARGIN or abs(output) > ERROR_MARGIN:
            print "WARNING calibration was unable to converge."
        else:
            print "Calibration complete."
            print "dB:{0:.2f}".format(feedback)
            print "Volume:{0:.0f}".format(round(volume))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print e
    finally:
        stream.stop_stream()
        stream.close()
        wav_to_play.close()
        spl.stop()
        if make_plot:
            plot(time_list, feedback_list, volume_list)

def main():
    parser = argparse.ArgumentParser(description='Calibrate system volume to specified dB as measured by SPL meter')
    parser.add_argument('--device', '-d', help='Playback device (System sound output MUST be set to this device)')
    parser.add_argument('--plot', '-p', action='store_true', default=False, help='Plot measured dB and volume level')
    parser.add_argument('spl_cmd', default=None, help='Command to run SPL meter')
    parser.add_argument('pb_file', help='Playback file')
    parser.add_argument('dB', type=float, help='Desired dB level')
    parser.add_argument('weight', choices=dB_weights)
    args = parser.parse_args()

    run(args.spl_cmd, args.dB, args.weight, args.pb_file, pb_device=args.device, make_plot=args.plot)


if __name__ == '__main__':
    main()
