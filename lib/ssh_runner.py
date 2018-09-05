#!/usr/bin/env python
import threading
import pexpect
from pexpect import pxssh
import time
import traceback
import re
import logging
from datetime import datetime


kill_commands = {
    'avsrun':'q'
}

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

    def __init__(self, label, ipaddress, username, password, wakeword, cmd, track_name,logger=None):
        self.label = label
        self.hostname = ipaddress
        self.username = username
        self.password = password
        self.t = StoppableThread(target=self.run)
        self.lock = threading.Lock()
        self.connected = False
        self.ssh = pexpect.pxssh.pxssh(timeout=None, ignore_sighup=False)
        self.start_cmd = cmd
        self.regex = re.compile(wakeword)
        self.done_regex = re.compile("Done")

        self.track_name = track_name

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
            print "{}".format(self.start_cmd)

            self.ssh.sendline("{}".format(self.start_cmd))

            while(True):
                if(self.t.stopped()):
                    self.logger.info("Stopped")
                    break
                time.sleep(2)


        except Exception as e:
            self.logger.error(str(e))
            self.logger.error(traceback.format_tb())


        finally:
            self.logger.info("Logging out")
            self.ssh.sendline(self.kill_cmd)
            self.ssh.prompt()
            lines = self.ssh.before
            self.logger.info(lines)
            self.ssh.logout()
            self.connected = False

    def reset(self):
        with self.lock:
            self._counter = 0
            self.last_time = datetime.now()

    def get_count(self):
        ssh_attempts = 5

        for i in range(ssh_attempts):
            try:
                
                count_ssh = pexpect.pxssh.pxssh(timeout=None, ignore_sighup=False)
                count_ssh.login(self.hostname, self.username, self.password)
                # print "mv /tmp/{} /media/r0ro/XMOS_Testing/".format(self.track_name)
                # count_ssh.sendline("mv /tmp/{} /media/r0ro/XMOS_Testing/".format(self.track_name))
                # count_ssh.prompt()
                # print "wakeword_sensory -w /media/r0ro/XMOS_Testing/{}".format(self.track_name)
                # count_ssh.sendline("wakeword_sensory -w /media/r0ro/XMOS_Testing/{}".format(self.track_name))
                # count_ssh.prompt()
                count_ssh.sendline("sox ~/Documents/{} temp_asr.wav remix 2".format(self.track_name))
                count_ssh.prompt()

                count_ssh.sendline("nc -w 3 10.128.28.36 10008 < temp_asr.wav")
                count_ssh.prompt()
                lines = count_ssh.before
                self.logger.info(lines)
                # print lines 
                self._counter = 0
                for line in lines.split('\n'):
                    if self.regex.search(line.strip()):
                        self._counter += 1
                    

                count_ssh.logout()
                break
            except pexpect.pxssh.ExceptionPxssh as e:
                time.sleep(5)
                if i == ssh_attempts-1:
                    raise

        connected = False
        return self._counter

    # def rename_track(self, track_name):
    #     rename_ssh = pexpect.pxssh.pxssh(timeout=None, ignore_sighup=False)
    #     rename_ssh.login(self.hostname, self.username, self.password)
    #     rename_ssh.sendline("mv test.raw {}".format(track_name))
    #     # rename_ssh.sendline("sox test.raw R_{} remix 2".format(track_name))
    #     rename_ssh.prompt()
    #     rename_ssh.logout()
    #     return


    def stop(self):
        self.t.stop()
        try:
            self.ssh.sendline(chr(3))
        except Exception:
            pass
        self.t.join(timeout=5)
        if self.t.is_alive():
            self.logger.info("Thread still alive. Sending Ctrl+C")

    def __del__(self):
        self.logger.info("Destructor called")
        self.t.stop()
