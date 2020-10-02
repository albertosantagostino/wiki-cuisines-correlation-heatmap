#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Various utility functions
"""

import pickle
import re

from itertools import islice


def execute_steps(STEPS, steps_to_run):
    """Run the specified program steps"""
    for step_idx in steps_to_run:
        print(f"Running {STEPS[step_idx].__name__}...")
        STEPS[step_idx]()


def save_to_file(file, obj):
    """Pickle the object and dump it to file"""
    with open(file, 'wb') as fp:
        pickle.dump(obj, fp)


def load_from_file(file):
    """Load a pickled object"""
    with open(file, 'rb') as fp:
        obj = pickle.load(fp)
    return obj


def strip_url(text):
    """Return the language prefix of the wiki URL"""
    result = re.search('://(.*)/wiki/', text)
    return result.group(1)


def split_to_chunks(data, nn):
    """Yield chunks of size nn from data"""
    if isinstance(data, list):
        for i in range(0, len(data), nn):
            yield data[i:i + nn]
    elif isinstance(data, dict):
        it = iter(data)
        for i in range(0, len(data), nn):
            yield {k: data[k] for k in islice(it, nn)}
