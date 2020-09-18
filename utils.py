#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import re


def save_to_file(file, obj):
    with open(file, 'wb') as fp:
        pickle.dump(obj, fp)


def load_from_file(file):
    with open(file, 'rb') as fp:
        obj = pickle.load(fp)
    return obj


def strip_url(text):
    result = re.search('://(.*)/wiki/', text)
    return result.group(1)


def execute_steps(STEPS, steps_to_run):
    for step_idx in steps_to_run:
        print(f"Running {STEPS[step_idx].__name__}...")
        STEPS[step_idx]()
