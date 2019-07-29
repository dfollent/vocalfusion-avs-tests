from __future__ import print_function

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import play_wav
import log_utils
import ssh_runner

import argparse
import json
import wave
import pyaudio
import numpy as np
import time
import threading
from datetime import datetime


OUTPUT_PATH = 'logs'
RUN_PLAY_LOOP = False
PLAY_LOOP_FINISHED = True


def get_basename(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]


def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)


def get_args():
    description = 'Run Amazon tests as defined by config file.'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('config', default=None, help='Test config file')
    return argparser.parse_args()


def stop_play_loop():
    global STOP_PLAY_LOOP_FLAG
    STOP_PLAY_LOOP_FLAG = False
    while PLAY_LOOP_FINISHED is False:
        time.sleep(1)


def play_loop(track, device, gain, channel):
    global STOP_PLAY_LOOP_FLAG
    global PLAY_LOOP_FINISHED

    STOP_PLAY_LOOP_FLAG = True
    PLAY_LOOP_FINISHED = False

    while STOP_PLAY_LOOP_FLAG:
        play_wav.play_gained_wav(track, device, gain, channel)
    PLAY_LOOP_FINISHED = True
        


def run_amazon_tests(config):

    pb_device = config['env_audio_host']['env_audio_speakers']
    dut_host = config['dut_host']
    tests = config['tests']    

    utterance_tracks = config['utterance_tracks']

    dut_ip = dut_host['ip']
    dut_name = dut_host['username']
    dut_password = dut_host['password']
    dut_rec_cmd = dut_host['dut_rec_cmd']

    rec_ssh_logger = log_utils.get_logger("_tmp", OUTPUT_PATH)

    try:

        for test in tests:
            test_name = test["name"]
            noise_track = test['noise_track']
            # utterance_tracks = test['utterance_tracks']
            noise_ch = int(test['noise_channel'])
            noise_gain = int(test['noise_gain'] if test['noise_gain'] else '0')
            utterance_ch = int(test['utterance_channel'])
            utterance_gain = int(test['utterance_gain'])

            for iteration in test['iterations']:

                if noise_track:
                    noise_track_thread = threading.Thread(target=play_loop, args=(noise_track, pb_device, noise_gain, noise_ch))
                    noise_track_thread.start()
                
                if utterance_tracks:
                    for utterance_track in utterance_tracks:

                        utterance_track_name = get_basename(utterance_track)
                        noise_track_name = get_basename(noise_track)
                        rec_track_name = "{}_{}_{}.wav".format(test_name, noise_track_name, utterance_track_name)

                        print(rec_track_name)

                        arecord_runner = ssh_runner.SshRunner(rec_track_name,
                                           dut_ip,
                                           dut_name,
                                           dut_password,
                                           wakeword="NA",
                                           cmd="{}{}".format(dut_rec_cmd, rec_track_name))

                        time.sleep(10)
                        try:
                            arecord_runner.start()
                            time.sleep(5)

                            play_wav.play_gained_wav(utterance_track, pb_device, utterance_gain, utterance_ch)
                            time.sleep(1)

                            arecord_runner.stop()

                        except KeyboardInterrupt:
                            arecord_runner.stop()
                            raise



                stop_play_loop()

    except Exception as e:
        stop_play_loop()
        raise




def main():
    
    args = get_args()
    
    try:
        config = get_json(args.config)
    except Exception as e:
        print('Error parsing JSON file!')
        raise


    run_amazon_tests(config)


if __name__ == '__main__':
    main()
