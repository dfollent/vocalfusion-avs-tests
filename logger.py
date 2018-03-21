#!/usr/bin/env python
import logging
import os

def get_logger(name, filepath, level=logging.DEBUG, console=False):
    try:
        os.makedirs(filepath)
    except Exception:
        pass

    formatter = logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.FileHandler('{}/{}.log'.format(filepath, name), mode='a')
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
