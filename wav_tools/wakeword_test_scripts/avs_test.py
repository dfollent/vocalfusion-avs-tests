#!/usr/bin/env python
import sys
import os
import argparse
import subprocess
from ssh_runner import ssh_runner
from ssh_runner import get_printer_logger
from play_wav import play_wav
import time
from datetime import datetime
import json
import traceback

log_filepath = 'logs'

def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def get_args(args):
    input_dict = get_json(args.config)
    avs_devices = input_dict['listening_devices']
    pb_device = input_dict['playback']['device']
    pb_files = input_dict['playback']['files']

    if 'iterations' in input_dict['playback']:
        iterations = input_dict['playback']['iterations']
    else:
        iterations = 1

    return avs_devices, pb_device, pb_files, iterations

def run_tests(avs_devices, pb_device, pb_files, loop_count):

    file_name = "{}_test_results".format(datetime.now().strftime('%Y%m%d'))
    file_path = 'logs'

    logger = get_printer_logger(file_name, file_path)
    runners = []
    try:
        for device in avs_devices:

            runner = ssh_runner(device.get('label'),
                                device.get('ip'),
                                device.get('username'),
                                device.get('password'),
                                device.get('wakeword'),
                                device.get('cmd'),
                                log_filepath)
            runners.append(runner)

        for runner in runners:
            runner.start()

        # Loop through file list
        for x in range(1, loop_count):
            # Loop through files
            for file in pb_files:
                time.sleep(5)
                for runner in runners:
                    runner.reset()

                logger.info("Running Test: {}".format(file))
                play_wav(file, pb_device)

                time.sleep(5)
                logger.info('**************************')
                logger.info("Test Complete: {}".format(file))
                for runner in runners:
                    logger.info("Count: {} - {} - {}".format(runner.get_count(), runner.label, runner.hostname))

                logger.info('**************************')

                for runner in runners:
                    if runner.connected is False:
                        raise Exception("Runner disconnected - {} - {}".format(runner.label, runner.hostname))

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")

    except Exception as e:
        logger.info("Exception:")
        logger.info(str(e))
        traceback.print_exc()


    finally:
        for runner in runners:
            runner.stop()

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--config',
                            default=None,
                            help='Config JSON file')

    (avs_devices, pb_device, pb_files, iterations) = get_args(argparser.parse_args())

    subprocess.call(["mosquitto_pub", "-t", "bored_room/door", "-m", "busy"])

    run_tests(avs_devices, pb_device, pb_files, iterations)

    subprocess.call(["mosquitto_pub", "-t", "bored_room/door", "-m", "idle"])
