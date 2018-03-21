#!/usr/bin/env python
import sys
import os
import argparse
import csv
import re
import glob

ROUND_ERROR = 10
WW_FAIL = 0
WW_SUCCESS = 1
WW_TOTAL = 100
WW_TIME_DIFF = 20
HEADER = ['DUT', 'Start Time']+ [x+1 for x in range(100)] + ['Total']

def create_outfile(filename):
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def get_seconds(time_delta):
    time_split = time_delta.split(':')
    return int(time_split[0])*60*60 + int(time_split[1])*60 + int(time_split[2])

def round_time_delta(num):
    x = int(num / WW_TIME_DIFF) * WW_TIME_DIFF
    rem = num % WW_TIME_DIFF
    if rem > ROUND_ERROR:
        x += WW_TIME_DIFF
    return x

def get_logdata(log_file):
    regex = re.compile(r'\((.*?)\)')
    test = []
    test_list = []
    for line in log_file:
        matches = regex.findall(line)
        if len(matches) >= 3:
            time_stamp = re.findall("(.*?)\s*\- \(", line)[0]
            time_delta = matches[0]
            count = matches[1]
            label = matches[2]

            if count == '01':
                # Finish entries for previous test
                if test:
                    for x in range(len(test), WW_TOTAL+2):
                        test.append(WW_FAIL)
                    test.append(test.count(WW_SUCCESS))
                # Begin new test
                test_list.append(test)
                test = [label, time_stamp]

            delta_s = get_seconds(time_delta)
            misses = (round_time_delta(delta_s) - WW_TIME_DIFF)/WW_TIME_DIFF
            for x in range(misses):
                test.append(WW_FAIL)

            test.append(WW_SUCCESS)

    # Reach EOF, finish entries for current test
    if test:
        for x in range(len(test), WW_TOTAL+2):
            test.append(WW_FAIL)
        test.append(test.count(WW_SUCCESS))
        test_list.append(test)

    return test_list

def main():
    parser = argparse.ArgumentParser(description='Parse AVS Client log to csv')
    parser.add_argument('log_filepath', help='Filename or directory of input logs')
    input_path = parser.parse_args().log_filepath

    if not os.path.exists(input_path):
        raise Exception('Error: Input file or directory does not exist.')

    basename = os.path.basename(input_path)
    out_filename = os.path.join('csv', os.path.splitext(basename)[0] + '.csv')
    create_outfile(out_filename)

    with open(out_filename, "a+b") as csvfile:

        if os.path.isfile(input_path):
            data = get_logdata(open(input_path))
            if data:
                csv.writer(csvfile).writerow(HEADER)
                csv.writer(csvfile).writerows(data)


        elif os.path.isdir(input_path):
            for input_file in os.listdir(input_path):
                if os.path.isdir(os.path.join(input_path, input_file)):
                    # TODO handle subdirectories, skip for now
                    continue
                data = get_logdata(open(os.path.join(input_path, input_file)))
                if data:
                    csv.writer(csvfile).writerow(HEADER)
                    csv.writer(csvfile).writerows(data)
                    csv.writer(csvfile).writerow('')


if __name__ == '__main__':
    main()
