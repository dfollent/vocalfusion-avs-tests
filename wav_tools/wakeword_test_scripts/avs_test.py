#!/usr/bin/env python
import sys
import os
import argparse
from ssh_runner import ssh_runner
from play_wav import play_wav
import time
import json
import traceback

def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def get_args(args):
    input_dict = get_json(args.config)
    avs_devices = input_dict['listening_devices']
    pb_device = input_dict['playback_device']
    pb_files = input_dict['playback_files']
    return avs_devices, pb_device, pb_files

def run_tests(avs_devices, pb_device, pb_files):
    runners = []
    try:
        for device in avs_devices:

            runner = ssh_runner(device.get('label'),
                                device.get('ip'),
                                device.get('username'),
                                device.get('password'),
                                device.get('wakeword'),
                                device.get('cmd'))
            runners.append(runner)

        for runner in runners:
            runner.start()

        # Loop through files
        for file in pb_files:
            time.sleep(5)
            print "Running Test: {}".format(file)
            play_wav(os.path.join('..', '..', 'audio', 'v1p7', file), pb_device)
            time.sleep(5)
            print "Test Complete: {}".format(file)
            for runner in runners:
                print "Count: {} - {}".format(runner.get_count(), runner.label)
                runner.reset_count()

    except KeyboardInterrupt:
        print "KeyboardInterrupt - run_tests()"

    except Exception as e:
        print "Exception: run_tests()"
        print str(e)
        traceback.print_exc()


    finally:
        for runner in runners:
            runner.stop()

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--config',
                            default=None,
                            help='Config JSON file')

    (avs_devices, pb_device, pb_files) = get_args(argparser.parse_args())
    run_tests(avs_devices, pb_device, pb_files)
