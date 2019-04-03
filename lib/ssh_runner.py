#!/usr/bin/env python
import sys
import threading
import paramiko
# import pexpect
# from pexpect import pxssh
import time
import traceback
import re
import logging
from datetime import datetime

import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, target=None):
        super(StoppableThread, self).__init__(target=target)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class SshRunner():
    """SSH Runner class. Runs a threaded command to a specified ssh target."""

    def __init__(self, label, ipaddress, username, password, wakeword, cmd, logger=None):
        self.label = label
        self.hostname = ipaddress
        self.username = username
        self.password = password

        self.t = StoppableThread(target=self.run)
        self.lock = threading.Lock()
        self.connected = False

        self.ssh_client = paramiko.client.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_shell = None

        self.cmd = cmd
        self.kill_cmd = chr(3)   # Ctrl+C interrupt

        if logger is not None:
            self.logger = logger
        else:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
            ch.setFormatter(formatter)
            self.logger = logging.getLogger(self.label)
            self.logger.addHandler(ch)


    def start(self):
        self.t.start()

    def run(self):
        try:
            self.ssh_client.connect(hostname=self.hostname, username=self.username, password=self.password)
            self.connected = True

            self.ssh_shell = self.ssh_client.invoke_shell()
            stdin = self.ssh_shell.makefile('wb')

            stdin.write(self.cmd + '\n')


            while(True):
                if(self.t.stopped()):
                    self.logger.info("Stopped")
                    break
                time.sleep(0.1)

            stdin.write(self.kill_cmd)
            stdin.flush()
            stdin.channel.close()

        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))


        finally:
            self.logger.info("Logging out")
            if self.ssh_shell is not None:
                self.ssh_shell.close()
            self.ssh_client.close()
            self.connected = False

    def stop(self):
        self.t.stop()
        self.t.join(timeout=5)
        if self.t.is_alive():
            self.logger.info("Thread still alive. Sending Ctrl+C")
            try:
                if self.ssh_shell is not None:
                    self.ssh_shell.close()
                self.ssh_client.close()
            except Exception:
                pass

    def __del__(self):
        self.logger.info("Destructor called")
        self.stop()
