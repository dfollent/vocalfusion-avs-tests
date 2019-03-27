#!/usr/bin/env python2

import argparse
import json
import wave
import pyaudio
import numpy as np
import time


def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)


def get_args():
    description = 'Run Amazon tests as defined by config file.'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('config', default=None, help='Test config file')
    
    return argparser.parse_args()

def play_loop(track, device, gain, channel):
    global PLAY_LOOP_FLAG
    PLAY_LOOP_FLAG = True
    
    while PLAY_LOOP_FLAG:
        play_gained_wav(track, device, gain, channel)
        


def run_amazon_tests(config):

    pb_device = input_dict['env_audio_host']['env_audio_speakers']
    dut_host = input_dict['dut_host']
    tests = input_dict['tests']    

    dut_ip = dut_host["ip"]
    dut_name = dut_host["username"]
    dut_password = dut_host["password"]

    for test in tests:
        noise_track = test['noise_track']
        utterance_tracks = test['utterance_tracks']
        noise_ch = int(test['noise_channel'])
        noise_gain = int(test['noise_gain'])
        utterance_ch = int(test['utterance_channel'])
        utterance_gain = int(test['utterance_gain'])

        for iteration in test['iterations']:
            play_loop(noise_track, pb_device, noise_gain, noise_ch)
            
            for utterance_track in utterance_tracks:
                time.sleep(5)
                play_wav.play_wav(utterance_track, pb_device, utterance_ch)
            
            global PLAY_LOOP_FLAG
            PLAY_LOOP_FLAG = False



def main():
    
    args = get_args()
    
    try:
        config = get_json(args.config)
    except Exception as e:
        print "Error parsing JSON file!"
        raise


    run_amazon_tests(config)


if __name__ == '__main__':
    main()
