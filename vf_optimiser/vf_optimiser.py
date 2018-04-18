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

PARAM_DICT = {'HPFONOFF': (0, 3),
              'AGCMAXGAIN': (0, 60),
              'AGCDESIREDLEVEL': (0, 1.0),
              'AGCTIME': (0.1, 1.0),
              'GAMMA_NN': (0.0, 3.0),
              'MIN_NN': (0.0 ,1.0),
              'GAMMA_NS': (0.0, 3.0),
              'MIN_NS': (0.0, 1.0)}

PI_LABEL = ''
PI_IPADDRESS = ''
PI_USER = ''
PI_PASSWORD = ''
PI_AVS_CMD = ''
PI_AVS_WW = ''
PB_DEVICE = ''
PB_FILE = []
VF_REBOOT_CMD = ''
VF_CTRL_UTIL = ''

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

def set_parameters(HPFONOFF, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS):
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login(PI_IPADDRESS, PI_USER, PI_PASSWORD)

    ssh.sendline(VF_CTRL_UTIL + ' HPFONOFF ' + str(HPFONOFF))
    ssh.sendline(VF_CTRL_UTIL + ' AGCMAXGAIN ' + str(AGCMAXGAIN))
    ssh.sendline(VF_CTRL_UTIL + ' AGCDESIREDLEVEL ' + str(AGCDESIREDLEVEL))
    ssh.sendline(VF_CTRL_UTIL + ' AGCTIME ' + str(AGCTIME))
    ssh.sendline(VF_CTRL_UTIL + ' GAMMA_NN ' + str(GAMMA_NN))
    ssh.sendline(VF_CTRL_UTIL + ' MIN_NN ' + str(MIN_NN))
    ssh.sendline(VF_CTRL_UTIL + ' GAMMA_NS ' + str(GAMMA_NS))
    ssh.sendline(VF_CTRL_UTIL + ' MIN_NS ' + str(MIN_NS))
    ssh.logout()


def run(HPFONOFF, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS):
    HPFONOFF_round = round(HPFONOFF)
    test_label = "{}_{}_{}_{}_{}_{}_{}_{}_{}_{}_{}".format(datetime.now().strftime('%Y%m%d'),
                                                           PI_LABEL, PB_FILE, HPFONOFF_round, AGCMAXGAIN,
                                                           AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN,
                                                           GAMMA_NS, MIN_NS)

    ssh_logger = log_utils.get_logger(test_label, OUTPUT_PATH)
    runner = ssh_runner.SshRunner(test_label,
                                   PI_IPADDRESS,
                                   PI_USER,
                                   PI_PASSWORD,
                                   PI_AVS_WW,
                                   PI_AVS_CMD,
                                   ssh_logger)
    result = 0
    try:
        runner.start()
        time.sleep(5)

        ssh_attempts = 5
        for i in range(ssh_attempts):
            try:
                reset_device()
                set_parameters(HPFONOFF_round, AGCMAXGAIN, AGCDESIREDLEVEL,
                               AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS)
                break
            except pxssh.ExceptionPxssh as e:
                time.sleep(5)
                if i == ssh_attempts-1:
                    raise

        for file in PB_FILE:
            play_wav.play_wav(file, PB_DEVICE)
            time.sleep(5)
            result = runner.get_count()
            print (result - prev_result)
            prev_result = result

        print
        runner.stop()

    except KeyboardInterrupt:
        runner.stop()
        raise
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        runner.stop()
        raise

    return result


def optimize(model, input_file, explore_file, output_file):
    bo = BayesianOptimization(run, PARAM_DICT)

    if input_file is not None and os.path.isfile(input_file):
        input_data = get_data(input_file)
        format_for_init(input_data)
        bo.initialize(input_data)

    if explore_file is not None and os.path.isfile(explore_file):
        explore_data = get_data(explore_file, remove_results=True)
        bo.explore(explore_data)

    bo.maximize(init_points=model["init_points"], n_iter=model["n_iterations"], kappa=model["kappa"])
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

    global PI_LABEL
    PI_LABEL = input_dict["listening_devices"]["label"]
    global PI_IPADDRESS
    PI_IPADDRESS = input_dict["listening_devices"]["ip"]
    global PI_USER
    PI_USER = input_dict["listening_devices"]["username"]
    global PI_PASSWORD
    PI_PASSWORD = input_dict["listening_devices"]["password"]
    global PI_AVS_CMD
    PI_AVS_CMD = input_dict["listening_devices"]["cmd"]
    global PI_AVS_WW
    PI_AVS_WW = input_dict["listening_devices"]["wakeword"]
    global PB_DEVICE
    PB_DEVICE = input_dict["playback"]["device"]
    global VF_REBOOT_CMD
    VF_REBOOT_CMD = input_dict["listening_devices"]["reboot_cmd"]
    global VF_CTRL_UTIL
    VF_CTRL_UTIL = input_dicta["listening_devices"]["ctrl_util"]

    for file in input_dict['playback']['files']:
        global PB_FILE
        PB_FILE = file
        optimize(input_dict["bayesian_model"], args.input, args.explore, args.output)



if __name__ == '__main__':
    main()
