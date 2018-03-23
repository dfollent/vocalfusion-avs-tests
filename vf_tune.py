#!/usr/bin/env python
import signal
import argparse
import subprocess
import ssh_runner
import time
import datetime
import traceback
import parameters
import log_utils
from pexpect import pxssh
import pexpect

OUTPUT_PATH = 'vf_tune_logs'

class vf_test():
    def __init__(self, _hpfonoff, _agcmaxgain, _agcdesiredlevel, _agctime, _gamma_nn, _min_nn, _gamma_ns, _min_ns):
         self.parameters = parameters.vf_parameters(_hpfonoff, _agcmaxgain, _agcdesiredlevel, _agctime, _gamma_nn, _min_nn, _gamma_ns, _min_ns)
         self.result = None

    def get_string(self):
        string = 'Test:'
        for parameter in self.parameters.list:
            string += ' ' + parameter.get_string()
        string += ' Result:'
        if self.result is None:
            string += 'NA'
        else:
            string += str(self.result)
        return string

def reset_device(test_logger):
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login('10.0.77.168', 'pi', 'raspberry')
    reboot_cmd = "~/sw_vocalfusion/host/dfu_control/bin/dfu_i2c reboot"
    ssh.sendline(reboot_cmd)
    test_logger.info(ssh.readline().strip())
    test_logger.info(ssh.readline().strip())

    ssh.logout()

def set_parameters(parameters):
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login('10.0.77.168', 'pi', 'raspberry')
    ctrl_util = "~/lib_xbeclear/lib_xbeclear/host/control/bin/vfctrl_i2c "

    ssh.sendline(ctrl_util + 'AGCGAIN ' + str(1))
    ssh.sendline(ctrl_util + 'AGCONOFF ' + str(0))

    for parameter in parameters.list:
        cmd = ctrl_util + parameter.cmd + ' ' + str(parameter.value)
        ssh.sendline(cmd)
    ssh.logout()


def run_avs(candidate, test_logger):
    music_path = '/Users/danielf/Music/outputL33.raw'
    pdm_play_cmd = ['/Users/danielf/vocalfusion/host_pdm_test_tools/pdm_play/bin/pdm_play', '-p', music_path]


    ssh_logger = log_utils.get_logger(candidate.get_string(), OUTPUT_PATH)
    test_logger.info("New Test:")

    runner = ssh_runner.ssh_runner(candidate.get_string(),
                        '10.0.77.168',
                        'pi',
                        'raspberry',
                        'Listening...',
                        'avsrun',
                        ssh_logger)

    ssh_attempts = 3
    for i in range(ssh_attempts):
        try:
            reset_device(test_logger)
            set_parameters(candidate.parameters)
            break
        except pexpect.pxssh.ExceptionPxssh as e:
            test_logger.error(str(e))
            test_logger.error(traceback.format_tb())
            if i == ssh_attempts-1:
                raise


    try:
        runner.start()
        time.sleep(5)
        process = subprocess.Popen(pdm_play_cmd)
        process.communicate()

        runner.stop()
        time.sleep(5)
        candidate.result = runner.get_count()
        test_logger.info(candidate.get_string())

    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        runner.stop()
        raise
    except Exception as e:
        test_logger.error(str(e))
        test_logger.error(traceback.format_tb())
        runner.stop()
        raise

def generatePopulation():
    population = []


    population.append(vf_test(1, 31.69, 0.082, 0.4444, 0.95, 0.036, 0.852, 0.331)) #49, 34


    population.append(vf_test(1, 31.6, 0.001, 0.982401, 3, 0.3, 1.0, 0.15)) #49, 34
    # population.append(vf_test(3, 60, 0.99, 0.5, 3.0, 0, 3.0, 0)) #41, 41, 44
    # population.append(vf_test(3, 60, 0.99, 0.5, 3.0, 0, 3.0, 0))

    # population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) #37, 40
    #
    # population.append(vf_test(0, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) #30
    # population.append(vf_test(2, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) #34
    # population.append(vf_test(3, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) #24
    #
    # population.append(vf_test(1, 20, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) #42
    population.append(vf_test(1, 40, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) # 30
    population.append(vf_test(1, 60, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.15)) # 44

    population.append(vf_test(1, 31.6, 0.1, 0.982401, 1.1, 0.3, 1.0, 0.15)) #46
    population.append(vf_test(1, 31.6, 0.2, 0.982401, 1.1, 0.3, 1.0, 0.15)) #44
    population.append(vf_test(1, 31.6, 0.4, 0.982401, 1.1, 0.3, 1.0, 0.15)) #43
    population.append(vf_test(1, 31.6, 0.8, 0.982401, 1.1, 0.3, 1.0, 0.15)) #42

    population.append(vf_test(1, 31.6, 0.001, 0.2, 1.1, 0.3, 1.0, 0.15)) #47
    population.append(vf_test(1, 31.6, 0.001, 0.4, 1.1, 0.3, 1.0, 0.15)) #39
    population.append(vf_test(1, 31.6, 0.001, 0.6, 1.1, 0.3, 1.0, 0.15)) #36
    population.append(vf_test(1, 31.6, 0.001, 0.8, 1.1, 0.3, 1.0, 0.15)) #41

    population.append(vf_test(1, 31.6, 0.001, 0.982401, 0, 0.3, 1.0, 0.15)) #47
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 2, 0.3, 1.0, 0.15)) #38
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 3, 0.3, 1.0, 0.15)) #49

    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.2, 1.0, 0.15)) #42
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.4, 1.0, 0.15)) #44
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.6, 1.0, 0.15)) #45
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.8, 1.0, 0.15)) #45

    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 0.0, 0.15))
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 2.0, 0.15))
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 3.0, 0.15))

    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.2))
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.4))
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.6))
    population.append(vf_test(1, 31.6, 0.001, 0.982401, 1.1, 0.3, 1.0, 0.8))

    population.append(vf_test(3, 60, 0.2, 0.2, 1.1, 0.3, 1.0, 0.15))


    return population

if __name__ == '__main__':

    output_file_name = "{}_test_results".format(datetime.datetime.now().strftime('%Y%m%d'))
    test_logger = log_utils.get_logger(output_file_name, OUTPUT_PATH, console=True)

    population = generatePopulation()
    for candidate in population:
        run_avs(candidate, test_logger)
