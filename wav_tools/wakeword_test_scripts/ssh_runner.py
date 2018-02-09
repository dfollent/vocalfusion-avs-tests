#!/usr/bin/env python
import threading
from stoppable_thread import stoppable_thread
from pexpect import pxssh
import pexpect
import getpass
import time
from datetime import datetime
import traceback
import re
import logging

kill_commands = {
    'avsrun':'q'
}


class ssh_runner():

    def __init__(self, label, ipaddress, username, password, wakeword, cmd, logpath):
        self.label = label
        self.hostname = ipaddress
        self.username = username
        self.password = password
        self.t = stoppable_thread(target=self.run)
        self.lock = threading.Lock()
        self.connected = False
        self.ssh = pxssh.pxssh(timeout=None, ignore_sighup=False)
        self.start_cmd = cmd
        self.regex = re.compile(wakeword)
        self._counter = 0

        if self.start_cmd in kill_commands:
            self.kill_cmd = kill_commands[self.start_cmd]
        else:
            self.kill_cmd = chr(3)   # Ctrl+C interrupt

        # if self.start_cmd == 'avsrun':
        #     self.kill_cmd = 'q'
        # else:
        #     self.kill_cmd = chr(3)   # Ctrl+C interrupt

        file_name = "{}_{}_{}".format(datetime.now().strftime('%Y%m%d'), 
                                   label.replace(" ","_").replace(".","_"),
                                   ipaddress.replace(".","_"))

        self.logger = get_logger(file_name, logpath)


    def start(self):
        self.t.start()

    def run(self):
        try:
            self.ssh.login(self.hostname, self.username, self.password)
            self.connected = True
            self.ssh.sendline(self.start_cmd)

            while(True):
                if(self.t.stopped()):
                    self.logger.info("Stopped")
                    break

                line = self.ssh.readline().strip()
                self.logger.info(line)

                if self.regex.search(line):
                    with self.lock:
                        self._counter += 1
                    output = '({:02}) ({}) {}'.format(self._counter, 
                                                      self.label, 
                                                      line)
                    print '{} {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), output)
                    self.logger.info(output)

        except Exception as e:
            # print "{} Exception:".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.Info("Exception:")
            # print "{} {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(e))
            self.logger.Info(str(e))

        finally:
            self.logger.info("Logging out")
            self.ssh.sendline(self.kill_cmd)
            self.ssh.logout()
            self.connected = False

    def reset_count(self):
        with self.lock:
            self._counter = 0

    def get_count(self):
        return self._counter

    def stop(self):
        self.t.stop()
        try:
            self.ssh.sendline(self.kill_cmd)
        except Exception:
            pass
        self.t.join(timeout=5)
        if self.t.is_alive():
            self.logger.info("Thread still alive. Sending Ctrl+C")

    def __del__(self):
        self.logger.info("Destructor called")
        self.t.stop()


def get_logger(name, filepath):
    try:
        os.mkdir(filepath)
    except Exception:
        pass

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('{}/{}.log'.format(filepath, name), mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(fh)
    return logger

def get_printer_logger(name, filepath):
    
    logger = get_logger(name, filepath)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(ch)
    return logger
