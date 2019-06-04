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



def get_basename(filepath):
	return os.path.splitext(os.path.basename(filepath))[0]


def create_ssh_client():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.connect(hostname=ip, username=username, password=password)
    return client

# print(os.path.isdir("/home/el"))
# print(os.path.exists("/home/el/myfile.txt"))


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
    argparser.add_argument('--ip', default='10.128.28.72', help='IP address of RPi')
    argparser.add_argument('--username', default='pi', help='SSH username of RPi')
    argparser.add_argument('--password', default='raspberry', help='SSH password of RPi')
    argparser.add_argument('--cmd', default='sudo bash sdk/startsample.sh', help='Command to run AVS SDK')
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

	# os.remove(tmp_wav)
	# os.remove(tmp_raw)


def run_sdk(ip, username, password, cmd, runtime=20):
	ssh = create_ssh_client()
	ssh.connect(hostname=ip, username=username, password=password)

	ssh_shell = ssh.invoke_shell()
	stdin = ssh_shell.makefile('wb')
	stdin.write(cmd + '\n')
	# transport = ssh.get_transport()
	# channel = transport.open_session()
	# channel.exec_command(cmd)
	# ssh.exec_command(cmd, get_pty=True)
	time.sleep(runtime)
	stdin.write('q' + '\n')
	stdin.flush()
	stdin.channel.close()
	ssh_shell.close()
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

    input_files = glob.glob("{}/*.wav".format(args.in_dir))

    for file in input_files:
       	print file
    	move_to_pi(file, args.channel, args.ip, args.username, args.password)
    	run_sdk(args.ip, args.username, args.password, args.cmd)

    	dest_file_raw = "{}/response_{}.raw".format(out_raw_dir, get_basename(file))
    	get_response_raw(dest_file_raw, args.ip, args.username, args.password)







if __name__ == '__main__':
    main()