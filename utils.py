#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Various utility functions
"""
import emoji
import json
import pickle
import re

from itertools import islice
from pathlib import Path


def get_flags_from_demonyms(country_demonyms):
    """Return a list of flags that correspond with the provided list of demonyms (adjectives)"""
    country_demonyms_lookup = json.load(open(Path('data/lookup_jsons/lookup_countries_demonyms.json'), 'r'))[0]
    flags = []
    for demonym in country_demonyms:
        try:
            country = country_demonyms_lookup[demonym].replace(' ', '_').replace('Cuisine of ', '')
            flag = emoji.emojize(f':{country}:', use_aliases=True)
            if flag == f':{country}:':
                flag = emoji.emojize(f':flag_for_{country}:', use_aliases=True)
            flags.append(flag)
        except KeyError:
            flags.append(f"{demonym}")
            print(f"Error getting flag for {demonym}")

    return flags


def get_languages_names(language_prefixes):
    """Return a list of extended language names given a list of 2-letters prefixes"""
    language_names = []
    lang_lookup_wl = load_from_file(Path('data/wiki_languages.dat'))
    lang_lookup_wl_dict = {kk: vv['eng_name'] for kk, vv in lang_lookup_wl.items()}
    for lang in language_prefixes:
        try:
            language_names.append(f"{lang_lookup_wl_dict[lang]}")
        except KeyError:
            language_names.append(f"{lang}")

    return language_names


def check_if_diagonal_value(mm, nn):
    """Check if cuisine and languages match and return cell text"""
    mm = emoji.demojize(mm, delimiters=('<<', '>>'))
    mm = re.sub(r'<<.*?>>', '', mm).strip()

    # From demonym to country
    country_demonyms_lookup = json.load(open(Path('data/lookup_jsons/lookup_countries_demonyms.json'), 'r'))[0]
    try:
        country = country_demonyms_lookup[mm]
    except KeyError:
        print(f"Unknown key ({mm})")
        return ''
    # From country to language
    country_languages_lookup = json.load(open(Path('data/lookup_jsons/lookup_countries_languages.json'), 'r'))[0]
    try:
        language = country_languages_lookup[country]
    except KeyError:
        print(f"Unknown key ({country})")
        return ''
    if language.lower() == nn.lower():
        return '<b>●</b>'
    else:
        return ''


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
