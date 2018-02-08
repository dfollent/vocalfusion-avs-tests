#!/usr/bin/env python
import threading
from stoppable_thread import stoppable_thread
from pexpect import pxssh
import pexpect
import getpass
import time
import traceback
import re


class ssh_runner():
    def __init__(self, label, ipaddress, username, password, wakeword, cmd):
        self.label = label
        self.hostname = ipaddress
        self.username = username
        self.password = password
        self.t = stoppable_thread(target=self.run)
        self.lock = threading.Lock()
        self.connected = False
        self.ssh = pxssh.pxssh(ignore_sighup=False)
        self.avs_kill_cmd = 'q'
        self.start_cmd = cmd
        self.regex = re.compile(wakeword)
        self._counter = 0


    def start(self):
        self.t.start()

    def run(self):
        try:
            self.ssh.login(self.hostname, self.username, self.password)
            self.connected = True
            self.ssh.sendline(self.start_cmd)

            while(True):
                if(self.t.stopped()):
                    print "Stopped"
                    break
                    
                line = self.ssh.readline().strip()
                # print line
                if self.regex.search(line):
                    with self.lock:
                        self._counter += 1
                    print '({}) ({}) {}'.format(self._counter,
                                                self.label,
                                                line)

        except Exception as e:
            print "Exception: ssh_runner.run()"
            print str(e)
            traceback.print_exc()

        finally:
            print "Logging out"
            self.ssh.sendline(self.avs_kill_cmd)
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
            self.ssh.sendline(self.avs_kill_cmd)
        except Exception:
            pass
        self.t.join(timeout=5)
        if self.t.is_alive():
            print "Thread still alive"

    def __del__(self):
        print "Destructor called"
        self.t.stop()


if __name__ == '__main__':
    try:
        runner = ssh_runner('AVS v1.4 I2S',
                           '10.0.77.108',
                           'pi',
                           'raspberry',
                           'avsrun',
                           'Listening...')

        runner.start()
        time.sleep(2)
        if runner.connected:
            time.sleep(20)
        print "Count - {}".format(runner.get_count())
        runner.reset_count()

    except KeyboardInterrupt:
        print "KeyboardInterrupt"

    except Exception as e:
        print "Exception"
        print str(e)
        traceback.print_exc()

    finally:
        runner.stop()
