#!/usr/bin/env python
import sys

class parameter():

    def __init__(self, cmd, value, min_value, max_value, increment):
        self.cmd = cmd
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.increment = increment
        if not self.valid_value():
            raise Exception('Invalid value.');

    def valid_value(self):
        return self.value >= self.min_value and self.value <= self.max_value

    def get_string(self):
        return self.cmd + ": " + str(self.value)

class hpfonoff(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'HPFONOFF', value, 0, 3, 1);

class agcmaxgain(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'AGCMAXGAIN', value, 0, 1000, 250);

class agcdesiredlevel(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'AGCDESIREDLEVEL', value, 0, 1, 0.1);

class agctime(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'AGCTIME', value, 0, 1.0, 0.1);

class gamma_nn(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'GAMMA_NN', value, 0, 3.0, 0.1);

class min_nn(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'MIN_NN', value, 0, 1.0, 0.1);

class gamma_ns(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'GAMMA_NS', value, 0, 3.0, 0.1);

class min_ns(parameter):
    def __init__(self, value):
        parameter.__init__(self, 'MIN_NS', value, 0, 1.0, 0.1);

class vf_parameters():
    def __init__(self, _hpfonoff, _agcmaxgain, _agcdesiredlevel, _agctime, _gamma_nn, _min_nn, _gamma_ns, _min_ns):
        self.list = [hpfonoff(_hpfonoff), agcmaxgain(_agcmaxgain), agcdesiredlevel(_agcdesiredlevel), agctime(_agctime), gamma_nn(_gamma_nn), min_nn(_min_nn), gamma_ns(_gamma_ns), min_ns(_min_ns)]
