#!/usr/bin/env python2
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import log_utils
import ssh_runner
import play_wav
from datetime import datetime
from bayes_opt import BayesianOptimization
from pexpect import pxssh
import traceback
import time
import argparse
import csv
import errno
import json

OUTPUT_PATH = 'logs'

# PARAM_DICT = {'HPFONOFF': (0, 3),
#               'AGCMAXGAIN': (0, 60),
#               'AGCDESIREDLEVEL': (0, 1.0),
#               'AGCTIME': (0.1, 1.0),
#               'GAMMA_NN': (0.0, 3.0),
#               'MIN_NN': (0.0 ,1.0),
#               'GAMMA_NS': (0.0, 3.0),
#               'MIN_NS': (0.0, 1.0)}

PARAM_DICT = {'HPFONOFF': (0, 3),
              'AGCDESIREDLEVEL': (0, 1.0),
              'AGCTIME': (0.1, 1.0),
              'ECHOONOFF': (0.45, 0.55),
              'AEC_REF_ATTEN': (-100, 0.0)}

PI_LABEL = ''
PI_IPADDRESS = ''
PI_USER = ''
PI_PASSWORD = ''
PI_APLAY_CMD = ''
PI_AREC_CMD = ''
PI_AVS_WW = ''
PB_DEVICE = ''
PB_FILE = ''
VF_REBOOT_CMD = ''
VF_CTRL_UTIL = ''
DEVICE_VOL = ''
WAIT_TIME = ''
VOLUME = ''

def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)


def write_rows(writer, rows):
    for row in rows:
        writer.writerow(row)

def export_data(data_dict, output_file):
    if output_file is None or data_dict is None or not data_dict['params']:
        return

    with open(output_file, "a+b") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([PI_LABEL])
        writer.writerow(list(data_dict['params'][0].keys()) + [data_dict.keys()[1]])
        write_rows(writer, [l.values()+[data_dict['values'][i]] for i, l in enumerate(data_dict['params'])])

def get_data(input_file, remove_results=False):
    data_dict = {}
    with open(input_file, "r+b") as csvfile:
        reader = csv.reader(csvfile)
        data_dict = {z[0]:filter(None, list(z[1:])) for z in zip(*reader)}
        data_dict = dict((key, val) for key, val in data_dict.iteritems() if val) # Remove empty keys
        for key in data_dict:
            data_dict[key] = map(float, data_dict[key]) # Cast from string to float

    if remove_results:
        data_dict.pop('values', None)

    return data_dict

def format_for_init(data_dict):
    data_dict['target'] = data_dict.pop('values', None)

def reset_device():
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login(PI_IPADDRESS, PI_USER, PI_PASSWORD)
    ssh.sendline(VF_REBOOT_CMD)
    ssh.logout()

def set_parameters(HPFONOFF, AGCDESIREDLEVEL, AGCTIME, ECHOONOFF, AEC_REF_ATTEN):
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login(PI_IPADDRESS, PI_USER, PI_PASSWORD)

    ssh.sendline(VF_CTRL_UTIL + ' HPFONOFF ' + str(HPFONOFF))
    ssh.sendline(VF_CTRL_UTIL + ' AGCDESIREDLEVEL ' + str(AGCDESIREDLEVEL))
    ssh.sendline(VF_CTRL_UTIL + ' AGCTIME ' + str(AGCTIME))
    ssh.sendline(VF_CTRL_UTIL + ' ECHOONOFF ' + str(ECHOONOFF))
    ssh.sendline(VF_CTRL_UTIL + ' AEC_REF_ATTEN ' + str(AEC_REF_ATTEN))

    ssh.logout()


def run(HPFONOFF, AGCDESIREDLEVEL, AGCTIME, ECHOONOFF, AEC_REF_ATTEN):
    HPFONOFF_round = round(HPFONOFF)
    ECHOONOFF_round = round(ECHOONOFF)
    test_label = "{}_{}_HOO_{}_ADL_{}_AT_{}_EOO{}_MA_{}".format(datetime.now().strftime('%Y%m%d'),
                                                           PI_LABEL, HPFONOFF_round, AGCDESIREDLEVEL, AGCTIME, ECHOONOFF_round, AEC_REF_ATTEN)

    ssh_logger = log_utils.get_logger(test_label, OUTPUT_PATH)
    rec_ssh_logger = log_utils.get_logger("{}_rec".format(test_label), OUTPUT_PATH)

    aplay_runner = ssh_runner.SshRunner(test_label,
                                   PI_IPADDRESS,
                                   PI_USER,
                                   PI_PASSWORD,
                                   PI_AVS_WW,
                                   PI_APLAY_CMD,
                                   ssh_logger)
    arecord_runner = ssh_runner.SshRunner(test_label,
                                   PI_IPADDRESS,
                                   PI_USER,
                                   PI_PASSWORD,
                                   PI_AVS_WW,
                                   PI_AREC_CMD,
                                   rec_ssh_logger)

    track_name = "V{}_T{}_HOO_{}_ADL_{}_AT_{}_EOO_{}_ARA_{}.raw".format(VOLUME, WAIT_TIME, HPFONOFF_round, AGCDESIREDLEVEL, AGCTIME, ECHOONOFF_round, AEC_REF_ATTEN)

    result = 0
    try:

        ssh_attempts = 5
        for i in range(ssh_attempts):
            try:
                reset_device()
                set_parameters(HPFONOFF_round, AGCDESIREDLEVEL, AGCTIME, ECHOONOFF_round, AEC_REF_ATTEN)
                break
            except pxssh.ExceptionPxssh as e:
                time.sleep(5)
                if i == ssh_attempts-1:
                    raise

        arecord_runner.start()
        aplay_runner.start()

        # Decide how long to wait
        time.sleep(float(WAIT_TIME))


        play_wav.play_wav(PB_FILE, PB_DEVICE)
        aplay_runner.stop()
        arecord_runner.stop()
        time.sleep(1)
        result = arecord_runner.get_count()
        arecord_runner.rename_track(track_name)

    except KeyboardInterrupt:
        aplay_runner.stop()
        arecord_runner.stop()
        raise
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        aplay_runner.stop()
        arecord_runner.stop()
        raise

    return result


def optimize(model, input_file, explore_file, output_file):
    bo = BayesianOptimization(run, pbounds=PARAM_DICT)

    if input_file is not None and os.path.isfile(input_file):
        input_data = get_data(input_file)
        format_for_init(input_data)
        bo.initialize(input_data)

    if explore_file is not None and os.path.isfile(explore_file):
        explore_data = get_data(explore_file, remove_results=True)
        bo.explore(explore_data)

    # print "{} {} {}".format(int(model["init_points"]), int(model["n_iterations"]), int(model["kappa"]))

    bo.maximize(init_points=int(model["init_rand_points"]), n_iter=int(model["n_iterations"]), kappa=int(model["kappa"]))
    export_data(bo.res['all'], output_file)


def main():

    parser = argparse.ArgumentParser(description='Bayesian Optimization of VocalFusion parameters')
    parser.add_argument('config', default=None, help='Config JSON file containing RPi, playback and bayesian model parameters')
    parser.add_argument('--output', '-o', help='Output CSV file')
    parser.add_argument('--input', '-i', help='Input CSV file')
    parser.add_argument('--explore', '-e', help='CSV file containing data points to explore')

    args = parser.parse_args()

    if args.input is not None and not os.path.isfile(args.input):
        raise Exception("Error - cannot find input file '{}'".format(args.input))

    if args.explore is not None and not os.path.isfile(args.explore):
        raise Exception("Error - cannot find explore input file '{}'".format(args.explore))

    try:
        input_dict = get_json(args.config)
    except Exception as e:
        print "Error parsing JSON file!"
        print (str(e))
        return

    global PI_LABEL
    PI_LABEL = input_dict["listening_devices"]["label"]
    global PI_IPADDRESS
    PI_IPADDRESS = input_dict["listening_devices"]["ip"]
    global PI_USER
    PI_USER = input_dict["listening_devices"]["username"]
    global PI_PASSWORD
    PI_PASSWORD = input_dict["listening_devices"]["password"]
    global PI_APLAY_CMD
    PI_APLAY_CMD = input_dict["listening_devices"]["play_cmd"]
    global PI_AREC_CMD
    PI_AREC_CMD = input_dict["listening_devices"]["rec_cmd"]
    global PI_AVS_WW
    PI_AVS_WW = input_dict["listening_devices"]["wakeword"]
    global PB_DEVICE
    PB_DEVICE = input_dict["playback"]["device"]
    global VF_REBOOT_CMD
    VF_REBOOT_CMD = input_dict["listening_devices"]["reboot_cmd"]
    global VF_CTRL_UTIL
    VF_CTRL_UTIL = input_dict["listening_devices"]["ctrl_util"]
    global DEVICE_VOL
    DEVICE_VOL = input_dict["device_volume"]


    wait_times = input_dict["wait_time"]

    for time in wait_times:
        global WAIT_TIME
        WAIT_TIME = time


        for volume in DEVICE_VOL:
            global VOLUME
            VOLUME = volume

            ssh_attempts = 5
            for i in range(ssh_attempts):
                try:
                    # Set volume
                    vol_ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
                    vol_ssh.login(PI_IPADDRESS, PI_USER, PI_PASSWORD)
                    vol_ssh.sendline("amixer sset 'Playback' {}%".format(volume))
                    vol_ssh.logout()  
                    break
                except pxssh.ExceptionPxssh as e:
                    time.sleep(5)
                    if i == ssh_attempts-1:
                        raise

            global PB_FILE
            PB_FILE = input_dict['playback']['files']

            print "Running Test - Wait Time:{}s - Volume:{}%".format(time, volume)
            optimize(input_dict["bayesian_model"], args.input, args.explore, "V{}_T{}_{}".format(volume, WAIT_TIME, args.output))



if __name__ == '__main__':
    main()
