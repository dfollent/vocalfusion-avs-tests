#!/usr/bin/env python
import threading
import pexpect
import time
import traceback
import re
import logging
from datetime import datetime


kill_commands = {
    'avsrun':'q'
}

class stoppable_thread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, target=None):
        super(stoppable_thread, self).__init__(target=target)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class ssh_runner():
    """SSH Runner class. Runs a threaded command to a specified ssh target."""

    def __init__(self, label, ipaddress, username, password, wakeword, cmd, logger=None):
        self.label = label
        self.hostname = ipaddress
        self.username = username
        self.password = password
        self.t = stoppable_thread(target=self.run)
        self.lock = threading.Lock()
        self.connected = False
        self.ssh = pexpect.pxssh.pxssh(timeout=None, ignore_sighup=False)
        self.start_cmd = cmd
        self.regex = re.compile(wakeword)
        self._counter = 0
        self.last_time = datetime.now()

        if self.start_cmd in kill_commands:
            self.kill_cmd = kill_commands[self.start_cmd]
        else:
            self.kill_cmd = chr(3)   # Ctrl+C interrupt

        if logger is not None:
            self.logger = logger
        else:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            self.logger = logging.getLogger(self.label)
            self.logger.addHandler(ch)


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

                    now = datetime.now()
                    time_diff_str = str(now - self.last_time).split('.')
                    self.last_time = now

                    output = '({}) ({:02}) ({}) {}'.format(time_diff_str[0],
                                                      self._counter,
                                                      self.label,
                                                      line)

                    # print '{} {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), output)
                    self.logger.info(output)

        except Exception as e:
            self.logger.error(str(e))
            self.logger.error(traceback.format_tb())


        finally:
            self.logger.info("Logging out")
            self.ssh.sendline(self.kill_cmd)
            self.ssh.logout()
            self.connected = False

    def reset(self):
        with self.lock:
            self._counter = 0
            self.last_time = datetime.now()

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
