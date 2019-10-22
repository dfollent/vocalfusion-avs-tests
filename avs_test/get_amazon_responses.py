from __future__ import print_function
import os
import errno
import argparse
import glob
import subprocess
import time

import paramiko
import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')
from scp import SCPClient


NUM_RETRY = 5


def get_basename(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]


def create_ssh_client():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return client


def check_dir_exists(directory):
    if not os.path.exists(directory):
        raise Exception("Input directory '{}' does not exist.".format(directory))


def create_dir(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def get_args():
    description = 'Run a directory of wav files through the AVS SDK on a pi'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('in_dir', default=None, help='Input directory')
    argparser.add_argument('--channel', type=int, default=1, help='Channel index of input wavs')
    argparser.add_argument('ip', help='IP address of RPi')
    argparser.add_argument('--username', default='pi', help='SSH username of RPi')
    argparser.add_argument('--password', default='raspberry', help='SSH password of RPi')
    argparser.add_argument('--cmd', default='sudo bash sdk-folder/startsample.sh', help='Command to run AVS SDK')
    argparser.add_argument('--op-point', type=int, default=5, help='Operating point')
    argparser.add_argument('--regex', default='*.wav', help='Regex for files in input directory')
    argparser.add_argument('out_dir', default=None, help='Output directory')
    return argparser.parse_args()


def move_to_pi(file, channel, ip, username, password):
    tmp_wav = "tmp.wav"
    tmp_raw = "tmp.raw"

    subprocess.call(["sox", file, tmp_wav, "remix", str(channel)])
    subprocess.call(["sox", tmp_wav, "-t", "raw", "-e", "signed-integer", "-r", "16000", "-b", "16", "-c", "1", tmp_raw])

    ssh = create_ssh_client()
    ssh.connect(hostname=ip, username=username, password=password)
    scp = SCPClient(ssh.get_transport())
    scp.put(tmp_raw, '/tmp/in.raw')
    scp.close()
    ssh.close()


def run_sdk(ip, username, password, cmd, runtime=20):
    ssh = create_ssh_client()
    ssh.connect(hostname=ip, username=username, password=password)
    for i in range(NUM_RETRY):
        try:
            ssh_shell = ssh.invoke_shell()
            stdin = ssh_shell.makefile('wb')
            stdin.write('sudo rm -f /tmp/out.raw\n')
            stdin.write(cmd + '\n')

            time.sleep(runtime)
            stdin.write('q' + '\n')
            stdin.flush()
            stdin.channel.close()
            ssh_shell.close()
            break
        except OSError as err:
            print("OS error: {0}".format(err))
    ssh.close()


def get_response_raw(dest_file, ip, username, password):
    ssh = create_ssh_client()
    ssh.connect(hostname=ip, username=username, password=password)
    scp = SCPClient(ssh.get_transport())
    scp.get('/tmp/out.raw', dest_file)
    scp.close()
    ssh.close()


def create_wav_copy(raw_filepath, wav_copy_filepath, rate=16000):
    subprocess.call(["sox", "-t", "raw", "-e", "signed-integer", "-b", "16", "-c", "1", "-r", "24000", raw_filepath, "-r", str(rate), wav_copy_filepath])


def main():
    args = get_args()
    check_dir_exists(args.in_dir)
    out_raw_dir = '{}/'.format(args.out_dir)
    create_dir(out_raw_dir)

    input_files = sorted(glob.glob("{}/{}".format(args.in_dir, args.regex)))

    for file in input_files:
        print(file)
        move_to_pi(file, args.channel, args.ip, args.username, args.password)
        run_sdk(args.ip, args.username, args.password, args.cmd + " " + str(args.op_point))

        dest_file_raw = "{}/response_{}.raw".format(out_raw_dir, get_basename(file))
        get_response_raw(dest_file_raw, args.ip, args.username, args.password)


if __name__ == '__main__':
    main()
