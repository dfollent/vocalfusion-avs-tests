#!/usr/bin/env python
import sys
import os
import argparse
import ssh_runner
import play_wav
import time

def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def get_args(args):
    input_dict = get_json(args.infile)
    avs_devices = input_dict['listening_devices']
    pb_device = input_dict['playback_device']
    pb_files = input_dict['playback_files']
    return avs_devices, pb_device, pb_files

def run_tests(avs_devices, pb_device, pb_files):
    try:
        print "Running Test: {}".format(file)

        runners = []
        for device in avs_devices:
            runners.append(ssh_runner(device.get('label'),
                                      device.get('ip'),
                                      device.get('username'),
                                      device.get('password'),
                                      device.get('wakeword')))

        for runner in runners:
            runner.start()

        # Loop through files
        for file in pb_files:
            time.sleep(5)
            play_wav(os.path.join('..', 'audio', 'v1p7', file), pb_device)
            print "Test Complete: {}".format(file)
            for runner in runners:
                print "{} - Count: {}".format(runner.label, runner.get_count())
                runner.reset_count()
    except KeyboardInterrupt:
        print "KeyboardInterrupt - run_tests()"

    finally:
        for runner in runners:
            runner.stop()

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--infile',
                            default=None,
                            help='Input JSON file')

    (avs_devices, pb_device, pb_files) = get_args(argparser.parse_args())
    run_tests(avs_devices, pb_device, pb_files)
