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


def reset_device(dut_ip, dut_name, dut_password, dut_reboot_cmd):
    for i in range(SSH_ATTEMPTS):
        try:
            ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
            ssh.login(dut_ip, dut_name, dut_password)
            ssh.sendline(dut_reboot_cmd)
            ssh.prompt()
            ssh.logout()
            break
        except pxssh.ExceptionPxssh as e:
            time.sleep(5)
            if i == SSH_ATTEMPTS-1:
                raise


def run_test(test, dut_host, pb_device):
    dut_label = dut_host["label"]
    dut_ip = dut_host["ip"]
    dut_name = dut_host["username"]
    dut_password = dut_host["password"]
    dut_wakeword = "NA"
    dut_reboot_cmd = dut_host["dut_reboot_cmd"]

    for iteration in test['iterations']:
        for dut_audio_track in test['dut_audio_tracks']:
            for env_audio_track in test['env_audio_tracks']:

                test_label = "{}_{}".format(datetime.now().strftime('%Y%m%d'), dut_label)
                ssh_logger = log_utils.get_logger(test_label, OUTPUT_PATH)
                rec_ssh_logger = log_utils.get_logger("{}_rec".format(test_label), OUTPUT_PATH)
                track_name = "{}_{}_{}_Take{}.wav".format(dut_label, (env_audio_track.split('.')[0]).split('/')[-1], (dut_audio_track.split('.')[0]).split('/')[-1],  iteration)
                dut_play_cmd = "{}{}".format(test['dut_play_cmd'], dut_audio_track)

                aplay_runner = ssh_runner.SshRunner(test_label,
                                               dut_ip,
                                               dut_name,
                                               dut_password,
                                               dut_wakeword,
                                               dut_play_cmd,
                                               track_name,
                                               ssh_logger)

                arecord_runner = ssh_runner.SshRunner(test_label,
                                               dut_ip,
                                               dut_name,
                                               dut_password,
                                               dut_wakeword,
                                               "{}{}".format(test['dut_rec_cmd'], track_name),
                                               track_name,
                                               rec_ssh_logger)

               
                try:
                    print datetime.now().strftime("%Y-%m-%d %H:%M")
                    reset_device(dut_ip, dut_name, dut_password, dut_reboot_cmd)
                    time.sleep(5)
                    arecord_runner.start()
                    aplay_runner.start()

                    time.sleep(float(test['delay_after_dut_audio']))

                    play_wav.play_wav(env_audio_track, pb_device)
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

    pb_device = input_dict['env_audio_host']['env_audio_speakers']
    dut_host = input_dict['dut_host']
    tests = input_dict['tests']

    for test in tests:
        print "\n *** \n"
        for i in test:
            print "{} {}".format(i, test[i])
        print "\n *** \n"

        run_test(test, dut_host, pb_device)


if __name__ == '__main__':
    main()
