#!/usr/bin/env python2
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import log_utils
import ssh_runner
import play_wav
from datetime import datetime
from pexpect import pxssh
import traceback
import time
import argparse
import csv
import errno
import json

OUTPUT_PATH = 'logs'
SSH_ATTEMPTS = 10

def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)

# def set_volume(dut_ip, dut_name, dut_password, vol):
    # for i in range(SSH_ATTEMPTS):
    #     try:
    #         # Set volume
    #         vol_ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    #         vol_ssh.login(dut_ip, dut_name, dut_password)
    #         vol_ssh.sendline("amixer sset 'Playback' {}%".format(volume))
    #         # vol_ssh.sendline("osascript -e 'set volume output volume {}'".format(vol))
    #         vol_ssh.logout()  
    #         break
    #     except pxssh.ExceptionPxssh as e:
    #         time.sleep(5)
    #         if i == SSH_ATTEMPTS-1:
    #             raiseu

def reset_device(dut_ip, dut_name, dut_password, reboot_cmd):
    for i in range(SSH_ATTEMPTS):
        try:
            ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
            ssh.login(dut_ip, dut_name, dut_password)
            ssh.sendline(reboot_cmd)
            ssh.prompt()
            ssh.logout()
            break
        except pxssh.ExceptionPxssh as e:
            time.sleep(5)
            if i == SSH_ATTEMPTS-1:
                raise


# def run_test(test, dut, pb_device):
#     test_output = "{}_avs_tester".format(datetime.now().strftime('%Y%m%d'))

#     logger = log_utils.get_logger(test_output, 'logs', console=True)
#     aplay_runners = []
#     arecord_runners = []

#     try:

#         for device in dut:
#             ssh_output = "{}_{}_{}".format(datetime.now().strftime('%Y%m%d'),
#                                    device.get('label').replace(" ","_").replace(".","_"),
#                                    device.get('ip').replace(".","_"))

#             ssh_logger = log_utils.get_logger(ssh_output, 'logs')
#             rec_ssh_logger = log_utils.get_logger("{}_rec".format(ssh_output), 'logs')

#             track_name = "{}_{}.wav".format(device.get('label'), (test_file.split('.')[0]).split('/')[-1])
#             rec_cmd = "{}{}".format(device.get('rec_cmd'), track_name)

#             aplay_runners.append(ssh_runner.SshRunner("{}_{}".format(device.get('label'), (test_file.split('.')[0]).split('/')[-1]),
#                                                 device.get('ip'),
#                                                 device.get('username'),
#                                                 device.get('password'),
#                                                 device.get('wakeword'),
#                                                 device.get('play_cmd'),
#                                                 track_name,
#                                                 ssh_logger))

#             arecord_runners.append(ssh_runner.SshRunner("{}_{}_rec".format(device.get('label'), (test_file.split('.')[0]).split('/')[-1]),
#                                                 device.get('ip'),
#                                                 device.get('username'),
#                                                 device.get('password'),
#                                                 device.get('wakeword'),
#                                                 rec_cmd,
#                                                 track_name,
#                                                 rec_ssh_logger))

#             # aplay_runners.append(aplay_runner)
#             # arecord_runners.append(arecord_runner)

#         for runner in arecord_runners:
#             runner.start()

#         for runner in aplay_runners:
#             runner.start()


#         print "Running Test: {}".format(test_file)
        
#         play_wav.play_wav(test_file, pb_device)

#         for runner in arecord_runners:
#             runner.stop()
#         for runner in aplay_runners:
#             runner.stop()

#         time.sleep(1)
#         print '**************************'
#         print "Test Complete: {}".format(test_file)

#         for runner in arecord_runners:
#             print "Count: {} - {} - {}".format(runner.get_count(), runner.label, runner.hostname)
#             # runner.rename_track(track_name)
#         print '**************************'

#         # for runner in runners:
#         #     if runner.connected is False:
#         #         raise Exception("Runner disconnected - {} - {}".format(runner.label, runner.hostname))

#     except KeyboardInterrupt:
#         logger.info("KeyboardInterrupt")
#         for runner in arecord_runners:
#             runner.stop()
#         for runner in aplay_runners:
#             runner.stop()

#     except Exception as e:
#         logger.error(str(e))
#         traceback.print_exc()

#     finally:
#         signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_test(test, dut, pb_device):
    dut_label = dut["label"]
    dut_ip = dut["ip"]
    dut_name = dut["username"]
    dut_password = dut["password"]
    dut_wakeword = dut["wakeword"]
    dut_reboot_cmd = dut["reboot_cmd"]

    for iteration in range(int(test['iterations'])):
        for dut_file in test['dut_files']:
            for test_file in test['files']:

                test_label = "{}_{}".format(datetime.now().strftime('%Y%m%d'), dut_label)
                ssh_logger = log_utils.get_logger(test_label, OUTPUT_PATH)
                rec_ssh_logger = log_utils.get_logger("{}_rec".format(test_label), OUTPUT_PATH)
                track_name = "{}_{}_{}_Take{}.wav".format(dut_label, (test_file.split('.')[0]).split('/')[-1], (dut_file.split('.')[0]).split('/')[-1],  iteration+3)
                play_cmd = "{}{}".format(test['play_cmd'], dut_file)

                aplay_runner = ssh_runner.SshRunner(test_label,
                                               dut_ip,
                                               dut_name,
                                               dut_password,
                                               dut_wakeword,
                                               play_cmd,
                                               track_name,
                                               ssh_logger)

                arecord_runner = ssh_runner.SshRunner(test_label,
                                               dut_ip,
                                               dut_name,
                                               dut_password,
                                               dut_wakeword,
                                               "{}{}".format(test['rec_cmd'], track_name),
                                               track_name,
                                               rec_ssh_logger)

               
                try:
                    print datetime.now().strftime("%Y-%m-%d %H:%M")
                    reset_device(dut_ip, dut_name, dut_password, dut_reboot_cmd)
                    time.sleep(5)
                    arecord_runner.start()
                    aplay_runner.start()

                    time.sleep(float(test['delay_after_dut_audio']))

                    play_wav.play_wav(test_file, pb_device)
                    aplay_runner.stop()
                    arecord_runner.stop()
                    time.sleep(1)

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

    # result = count / ITERATIONS
    return

def main():
    description = 'Run AVS tests as defined by config file. Log client output(s) and test results.'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('config', default=None, help='Config JSON file')

    try:
        input_dict = get_json(argparser.parse_args().config)
    except Exception as e:
        print "Error parsing JSON file!"
        raise

    pb_device = input_dict['playback']['device']
    dut = input_dict['dut']
    tests = input_dict['tests']

    for test in tests:
        print "\n *** \n"
        for i in test:
            print "{} {}".format(i, test[i])
        print "\n *** \n"

        run_test(test, dut, pb_device)



    # for test_file in test_files:
    #     run_tests(dut, pb_device, test_file)


if __name__ == '__main__':
    main()
