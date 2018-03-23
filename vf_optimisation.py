import datetime
import log_utils
from bayes_opt import BayesianOptimization
from pexpect import pxssh
import ssh_runner
import subprocess
import traceback
import time

OUTPUT_PATH = 'vf_tune_logs'

PARAM_DICT = {'HPFONOFF': (0, 3),
              'AGCMAXGAIN': (0, 60),
              'AGCDESIREDLEVEL': (0, 1.0),
              'AGCTIME': (0.1, 1.0),
              'GAMMA_NN': (0.0, 3.0),
              'MIN_NN': (0.0 ,1.0),
              'GAMMA_NS': (0.0, 3.0),
              'MIN_NS': (0.0, 1.0)}

PI_IP_ADDRESS = '10.0.77.168'
PI_USER = 'pi'
PI_PASSWORD = 'raspberry'

def reset_device():
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login('10.0.77.168', 'pi', 'raspberry')
    reboot_cmd = "~/sw_vocalfusion/host/dfu_control/bin/dfu_i2c reboot"
    ssh.sendline(reboot_cmd)
    print(ssh.readline().strip())
    print(ssh.readline().strip())

    ssh.logout()

def set_parameters(HPFONOFF, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS):
    ctrl_util = "~/lib_xbeclear/lib_xbeclear/host/control/bin/vfctrl_i2c "
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login(PI_IP_ADDRESS, PI_USER, PI_PASSWORD)

    ssh.sendline(ctrl_util + 'HPFONOFF ' + str(HPFONOFF))
    ssh.sendline(ctrl_util + 'AGCMAXGAIN ' + str(AGCMAXGAIN))
    ssh.sendline(ctrl_util + 'AGCDESIREDLEVEL ' + str(AGCDESIREDLEVEL))
    ssh.sendline(ctrl_util + 'AGCTIME ' + str(AGCTIME))
    ssh.sendline(ctrl_util + 'GAMMA_NN ' + str(GAMMA_NN))
    ssh.sendline(ctrl_util + 'MIN_NN ' + str(MIN_NN))
    ssh.sendline(ctrl_util + 'GAMMA_NS ' + str(GAMMA_NS))
    ssh.sendline(ctrl_util + 'MIN_NS ' + str(MIN_NS))
    ssh.logout()


def run_test(HPFONOFF, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS):
    HPFONOFF_round = round(HPFONOFF)
    music_path = '/Users/danielf/Music/outputL33.raw'
    pdm_play_cmd = ['/Users/danielf/vocalfusion/host_pdm_test_tools/pdm_play/bin/pdm_play', '-p', music_path]

    test_label = "{}_{}_{}_{}_{}_{}_{}_{}_{}".format(datetime.datetime.now().strftime('%Y%m%d'), HPFONOFF_round, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS)

    ssh_logger = log_utils.get_logger(test_label, OUTPUT_PATH)


    runner = ssh_runner.ssh_runner(test_label,
                        '10.0.77.168',
                        'pi',
                        'raspberry',
                        'Listening...',
                        'avsrun',
                        ssh_logger)

    ssh_attempts = 3
    for i in range(ssh_attempts):
        try:
            reset_device()
            set_parameters(HPFONOFF_round, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS)
            break
        except pexpect.pxssh.ExceptionPxssh as e:
            print(str(e))
            print(traceback.format_tb())
            if i == ssh_attempts-1:
                raise

    result = 0
    try:
        runner.start()
        process = subprocess.Popen(pdm_play_cmd)

        process.communicate()

        runner.stop()
        time.sleep(5)
        result = runner.get_count()

    except KeyboardInterrupt:
        runner.stop()
        raise
    except Exception as e:
        print(str(e))
        print(traceback.format_tb())
        runner.stop()
        raise

    return result

def main():

    bo = BayesianOptimization(run_test, PARAM_DICT)
    bo.initialize(
        {
            'target':[41, 42, 30, 44, 46, 44, 43, 42, 47, 39, 36, 41, 47, 38, 40, 42, 44, 45, 45, 42, 30, 39, 47, 34],
            'HPFONOFF':[3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.3717, 1.6891, 0.0268, 0.9135, 2.3053],
            'AGCMAXGAIN': [60, 20, 40 ,60, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 31.6, 44.0491, 41.5714, 58.9181, 21.8730, 30.4777],
            'AGCDESIREDLEVEL': [0.99, 0.001, 0.001, 0.001, 0.1, 0.2, 0.4, 0.8, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.2618, 0.5314, 0.8606, 0.526, 0.8927],
            'AGCTIME': [0.5, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.2, 0.4, 0.6, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.982401, 0.9719, 0.9427, 0.9638, 0.1718, 0.3171],
            'GAMMA_NN': [3.0, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 0, 2, 3, 1.1, 1.1, 1.1, 1.1, 1.8264, 1.7382, 2.9474, 0.9015, 1.9919],
            'MIN_NN': [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.2, 0.4, 0.6, 0.8, 0.4887, 0.2361, 0.2654, 0.6471, 0.3934],
            'GAMMA_NS': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.3318, 1.4049, 1.2105, 1.4045, 0.2902],
            'MIN_NS': [0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.2624, 0.8133, 0.9746, 0.0872, 0.5138]
        }
    )

    bo.maximize(init_points=2, n_iter=20, kappa=3)
    print(bo.res['max'])

if __name__ == '__main__':
    main()
