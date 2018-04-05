import os
import signal
import subprocess
import argparse
import threading
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import spline
from ssh_runner import stoppable_thread
import play_wav
import pyaudio
import wave


MAX_VOLUME = 60
STEPS = 60
EPSILON = 0.5
REQ_STABILITY = 10

class spl_meter():
    def __init__(self, cmd):
        self.value = 0.0
        self._stop_event = threading.Event()
        self.cmd = cmd
        self.thread = stoppable_thread(target=self.run)
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.stop()
        self.thread.join(timeout=2)

    def run(self):
        process = subprocess.Popen(self.cmd.split(), env=os.environ.copy(),
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while(True):
            line = process.stdout.readline()
            if line != '':
                self.running = True
                self.value = (5*self.value + float(line)) / 6
            else:
                break

            if self.thread.stopped():
                break

        os.kill(process.pid, signal.SIGINT)

    def get_value(self):
        return self.value

    def __del__(self):
        self.thread.stop()

def pi_controller(y, yc, h=1, Kp=1, Ti=1, u0=0, e0=0):
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
def getVolume():
    cmd = ["osascript", "-e", "output volume of (get volume settings)"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    line = process.stdout.readline()
    return float(line)

# Set volume in range 0 - 100
def setVolume(volume):
    volume = min(round(volume), MAX_VOLUME)
    subprocess.call(["osascript", "-e", "set volume output volume {}".format(volume)])

def get_audio_stream(pb_file, pb_device):
    audio_out = pyaudio.PyAudio()
    wav_to_play = wave.open('white_noise.wav', 'rb')

    audio_out_index = None
    if pb_device is not None:
        audio_out_index = play_wav.select_device(audio_out, pb_device, 'Output')


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
    # time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)
    # feedback_smooth = spline(time_list, feedback_list, time_smooth)
    # volume_smooth = spline(time_list, volume_list, time_smooth)

    # plt.plot(time_smooth, feedback_smooth)
    # plt.plot(time_smooth, volume_smooth)
    plt.plot(time_list, feedback_list, label='Feedback (dB)')
    plt.plot(time_list, volume_list, label='Volume')
    plt.legend()
    # plt.legend(handles=[f, line_down])
    #
    # plt.xlim((0, length(feedback_list)+1))
    plt.ylim((min(min(feedback_list), min(volume_list))-1, max(max(feedback_list), max(volume_list))+1))
    plt.xlabel('Ticks (0.3s)')
    plt.ylabel('Levels')
    plt.title('SPL Calibration')

    plt.grid(True)
    plt.show()

def run(spl_cmd, setpoint, pb_file, pb_device=None):
    spl = spl_meter(spl_cmd)
    spl.start()
    time.sleep(5)
    if spl.running == False:
        spl.stop()
        raise Exception('SPL device is not running, cannot proceed.')

    wav_to_play, stream = get_audio_stream(pb_file, pb_device)
    stream.start_stream()
    time.sleep(3)

    feedback_list = []
    time_list = []
    volume_list = []

    try:
        volume = getVolume()
        error = 0
        output = 0
        stability_count = 0
        feedback = 0
        i = 1
        # for i in range(1, STEPS):
        while stream.is_active():
            feedback = spl.get_value()
            error = setpoint - feedback

            input_generator = pi_controller(feedback, setpoint, h=0.3, Kp=0.2, Ti=3.5, e0=error)
            output = next(input_generator)

            if abs(error) <= EPSILON and abs(output) <= EPSILON:
                stability_count += 1
                if stability_count >= REQ_STABILITY:
                    break
            else:
                stability_count = 0

            volume = volume + output
            adj_volume = min(100, max(0, round(volume)))
            setVolume(adj_volume)

            feedback_list.append(feedback)
            time_list.append(i)
            volume_list.append(adj_volume)
            # Guarantee loop period of 0.3s
            time.sleep(0.3 - (time.time() % 0.3))
            i += 1

        if error > EPSILON or output > EPSILON:
            print "Warning: calibration was unable to converge. Try adjusting control parameters."
        else:
            print "Calibration complete."
            print "dB: {0:.2f}".format(feedback)
            print "Volume: {0:.0f}".format(round(volume))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print e
    finally:
        stream.stop_stream()
        stream.close()
        wav_to_play.close()
        spl.stop()
        plot(time_list, feedback_list, volume_list)

def main():
    parser = argparse.ArgumentParser(description='Calibrate system to specified dB')
    parser.add_argument('cmd', default=None, help='Command to run SPL device')
    parser.add_argument('pb_file', help='Playback file')
    parser.add_argument('--device', '-d', help='Playback device')
    parser.add_argument('dB', type=float, help='Desired dB level')
    args = parser.parse_args()

    run(args.cmd, args.dB, args.pb_file, args.device)


if __name__ == '__main__':
    main()
