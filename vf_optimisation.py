import datetime
import log_utils
from bayes_opt import BayesianOptimization
import pexpect
from pexpect import pxssh
import ssh_runner
import subprocess
import traceback
import time
import play_wav

OUTPUT_PATH = 'vf_tune_logs'

PARAM_DICT = {'HPFONOFF': (0, 3),
              'AGCMAXGAIN': (0, 60),
              'AGCDESIREDLEVEL': (0, 1.0),
              'AGCTIME': (0.1, 1.0),
              'GAMMA_NN': (0.0, 3.0),
              'MIN_NN': (0.0 ,1.0),
              'GAMMA_NS': (0.0, 3.0),
              'MIN_NS': (0.0, 1.0)}
 
PI_IP_ADDRESS = '10.128.20.13' #'10.0.77.168'
PI_USER = 'pi'
PI_PASSWORD = 'raspberry'
PB_DEVICE = "xCORE-AUDIO Hi-Res 2"

def reset_device():
    ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
    ssh.login(PI_IP_ADDRESS, PI_USER, PI_PASSWORD)
    reboot_cmd = "~/sw_vocalfusion/host/dfu_control/bin/dfu_i2c reboot"
    ssh.sendline(reboot_cmd)
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
    music_path = '/Users/xmos/sandboxes/vocalfusion-tests-scratch/audio/v1p7/Short_Test.wav'
    pdm_play_cmd = ['/Users/danielf/vocalfusion/host_pdm_test_tools/pdm_play/bin/pdm_play', '-p', music_path]

    test_label = "{}_{}_{}_{}_{}_{}_{}_{}_{}".format(datetime.datetime.now().strftime('%Y%m%d'), HPFONOFF_round, AGCMAXGAIN, AGCDESIREDLEVEL, AGCTIME, GAMMA_NN, MIN_NN, GAMMA_NS, MIN_NS)

    ssh_logger = log_utils.get_logger(test_label, OUTPUT_PATH)


    runner = ssh_runner.ssh_runner(test_label,
                        PI_IP_ADDRESS,
                        PI_USER,
                        PI_PASSWORD,
                        'Listening...',
                        'avsrun',
                        ssh_logger)


    result = 0
    try:
        runner.start()
        # process = subprocess.Popen(pdm_play_cmd)
        # process.communicate()
        time.sleep(5)
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


        play_wav.play_wav(music_path, PB_DEVICE)

        time.sleep(5)
        runner.stop()
        result = runner.get_count()

    except KeyboardInterrupt:
        runner.stop()
        raise
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        runner.stop()
        raise

    return result

def main():

    results_logger = log_utils.get_logger("{}_vf_opt_results".format(datetime.datetime.now().strftime('%Y%m%d')), OUTPUT_PATH, console=True)
    bo = BayesianOptimization(run_test, PARAM_DICT)

    bo.maximize(init_points=10, n_iter=80, kappa=4)

    results_logger.info('Max Result:')
    results_logger.info(bo.res['max'])
    results_logger.info('All Results:')
    results_logger.info(bo.res['all'])
   

if __name__ == '__main__':
    main()
