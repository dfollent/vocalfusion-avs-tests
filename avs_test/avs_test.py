#!/usr/bin/env python2
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import log_utils
import ssh_runner
import play_wav
import argparse
import subprocess
import time
from datetime import datetime
import json
import traceback

def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def get_args(args):
    try:
        input_dict = get_json(args.config)
    except Exception as e:
        print "Error parsing JSON file!"
        raise

    pb_device = input_dict['playback']['device']
    pb_files = input_dict['playback']['files']

    if 'iterations' in input_dict['playback']:
        iterations = input_dict['playback']['iterations']
    else:
        iterations = 1

    return avs_devices, pb_device, pb_files, iterations

def run_tests(avs_devices, pb_device, pb_files, loop_count):
    test_output = "{}_avs_tester".format(datetime.now().strftime('%Y%m%d'))
    ssh_output = "{}_{}_{}".format(datetime.now().strftime('%Y%m%d'),
                                   label.replace(" ","_").replace(".","_"),
                                   ipaddress.replace(".","_"))
    logger = log_utils.get_logger(test_file_name, 'logs', console=True)
    ssh_logger = log_utils.get_logger(ssh_output, 'ssh_logs')
    runners = []

    try:
        subprocess.call(["mosquitto_pub", "-t", "bored_room/door", "-m", "busy"])

        for device in avs_devices:
            runners.append(ssh_runner.SshRunner(device.get('label'),
                                                device.get('ip'),
                                                device.get('username'),
                                                device.get('password'),
                                                device.get('wakeword'),
                                                device.get('cmd'),
                                                ssh_logger))
            for runner in runners:
                runner.start()

        # Loop through file list
        for x in range(loop_count):
            # Loop through files
            for pb_file in pb_files:
                time.sleep(5)
                for runner in runners:
                    runner.reset()

                logger.info("Running Test: {}".format(pb_file))
                play_wav.play_wav(pb_file, pb_device)

                time.sleep(5)
                logger.info('**************************')
                logger.info("Test Complete: {}".format(pb_file))

                for runner in runners:
                    logger.info("Count: {} - {} - {}".format(runner.get_count(), runner.label, runner.hostname))
                logger.info('**************************')

                for runner in runners:
                    if runner.connected is False:
                        raise Exception("Runner disconnected - {} - {}".format(runner.label, runner.hostname))

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")

    except Exception as e:
        self.logger.error(str(e))
        self.logger.error(traceback.format_tb())

    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        for runner in runners:
            runner.stop()
        subprocess.call(["mosquitto_pub", "-t", "bored_room/door", "-m", "idle"])

def main():
    description = 'Run AVS tests as defined by config file. Log client output(s) and test results.'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('config',
                            default=None,
                            help='Config JSON file')
    run_tests(get_args(argparser.parse_args()))


if __name__ == '__main__':
    main()
