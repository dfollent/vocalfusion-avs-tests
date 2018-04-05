import os
import signal
import subprocess
import argparse
import threading
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import spline
import pid
from ssh_runner import stoppable_thread

MAX_VOLUME = 95
STEPS = 60

class spl_meter():
    def __init__(self, cmd):
        self.value = 0.0
        self._stop_event = threading.Event()
        self.cmd = cmd
        self.thread = stoppable_thread(target=self.run)
        self.lock = threading.Lock()

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
                new_val = (5*self.value + float(line)) / 6
                with self.lock:
                    self.value = new_val
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

def main():
    parser = argparse.ArgumentParser(description='Calibrate system to specified dB')
    parser.add_argument('cmd', default=None, help='Command to invoke measurement device')
    parser.add_argument('dB', type=float, help='Desired dB level')
    args = parser.parse_args()
    cmd = args.cmd

    spl = spl_meter(cmd)
    spl.start()
    time.sleep(4)

    feedback_list = []
    time_list = []
    volume_list = []

    setpoint = args.dB
    volume = getVolume()

    for i in range(1, STEPS):
        feedback = spl.get_value()

        input_generator = pi_controller(feedback, setpoint, h=0.3, Kp=0.2, Ti=3.5, e0=setpoint-feedback)

        volume = volume + next(input_generator)
        setVolume(volume)

        feedback_list.append(feedback)
        time_list.append(i)
        volume_list.append(volume)
        # Guarantee loop period of 0.3s
        time.sleep(0.3 - (time.time() % 0.3))

    spl.stop()

    time_sm = np.array(time_list)
    time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)
    feedback_smooth = spline(time_list, feedback_list, time_smooth)
    volume_smooth = spline(time_list, volume_list, time_smooth)

    plt.plot(time_smooth, feedback_smooth)
    plt.plot(time_smooth, volume_smooth)
    plt.plot(time_list, feedback_list)
    plt.plot(time_list, volume_list)


    plt.xlim((0, STEPS))
    plt.ylim((min(min(feedback_list), min(volume_list))-1, max(max(feedback_list), max(volume_list))+1))
    plt.xlabel('time (s)')
    plt.ylabel('PID (PV)')
    plt.title('TEST PID')

    plt.grid(True)
    plt.show()

    # while(True):
    #     print "{0:.2f}".format(spl.get_value())
    #     time.sleep(1)


if __name__ == '__main__':
    main()
