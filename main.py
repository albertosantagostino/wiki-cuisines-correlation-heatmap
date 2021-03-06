#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to create an heatmap between Wikipedia cuisines pages
"""

import pandas as pd
import numpy as np
import requests

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import unquote
from tqdm import tqdm

import defs
from utils import strip_url, save_to_file, load_from_file, execute_steps, split_to_chunks
from visualization import step5_create_plots


def step1_prepare_cuisines_data():
    """Create a data structure starting from the cuisines list in Template:Cuisines"""
    req = requests.get('https://en.wikipedia.org/wiki/Template:Cuisines')
    soup = BeautifulSoup(req.text, features='html.parser')
    html_cuisines = soup.find(title='National dish').find_next('ul')
    cuisines_titles = []
    skipped = []
    for ch in html_cuisines:
        if not isinstance(ch, str):
            if len(ch.find_all('a')) > 1:
                # If it has sub-cuisines (regional ones) consider only the first
                cuisine = ch.find_all('a')[0]
            else:
                # If it's only a national cuisine
                cuisine = ch.find('a')
            # If it's not a redirect to a different page (e.g.: "cuisine" section in the country page)
            if not cuisine.get('class'):
                title, href = cuisine.get('title'), cuisine.get('href')
                cuisines_titles.append((title, unquote(href.replace('/wiki/', ''))))
            elif 'mw-redirect' in cuisine.get('class'):
                skipped.append(cuisine.get('title'))
            else:
                raise ValueError(f"Undefined case: {cuisine}")
    if skipped:
        for skip in skipped:
            print(f"[Skip] {skip} (redirect)")

    api_url = 'https://en.wikipedia.org/w/api.php'
    params = {'action': 'query', 'format': 'json'}
    cuisines_raw = {}
    for chunk in split_to_chunks(cuisines_titles, 50):
        params['titles'] = f"{'|'.join([c[1] for c in chunk])}"
        with requests.Session() as session:
            post = session.post(api_url, params)
            res = post.json()
        for vv in res['query']['pages'].values():
            cuisines_raw[vv['title']] = {'pageid': str(vv['pageid']), 'languages': {}}
    save_to_file('data/cuisines_raw.dat', cuisines_raw)


def step2_populate_other_languages():
    """Gets URLs and titles of cuisines in multiple languages"""
    cuisines_raw = load_from_file('data/cuisines_raw.dat')

    wiki_url = 'https://en.wikipedia.org/w/api.php'
    params = {'action': 'query', 'prop': 'langlinks|info', 'llprop': 'url', 'lllimit': 'max', 'format': 'json'}
    print("Getting links for every cuisine for every language...")
    for vv in tqdm(cuisines_raw.values()):
        pageid = vv['pageid']
        params['pageids'] = pageid
        with requests.Session() as session:
            post = session.post(wiki_url, params)
            res = post.json()
            res_info = res['query']['pages'][pageid]
        if 'langlinks' in res_info:
            vv['languages'] = {
                vv['lang']: {
                    'title': vv['*'],
                    'wiki_url': strip_url(vv['url'])
                }
                for vv in res_info['langlinks']
            }
            vv['languages']['en'] = {}
            vv['languages']['en']['length'] = res_info['length']
            vv['languages']['en']['title'] = res['query']['pages'][pageid]['title']
    save_to_file('data/cuisines_langs.dat', cuisines_raw)


def step3_fill_lengths():
    """Retrieve the lengths of the pages via APIs"""
    cuisines = load_from_file('data/cuisines_langs.dat')

    # TODO: refactor grouping together pages, do only one request for every xyz.wikipedia.org
    params = {'action': 'query', 'prop': 'info', 'format': 'json'}
    skipped = []
    for kk, vv in tqdm(cuisines.items()):
        for lang_prefix, page in tqdm(vv['languages'].items()):
            if lang_prefix != 'en':
                wiki_url = page['wiki_url']
                api_url = f'https://{wiki_url}/w/api.php'
                params['titles'] = page['title']
                with requests.Session() as session:
                    post = session.post(api_url, params)
                    if post.ok:
                        res = post.json()
                    else:
                        print("Issue in POST call")
                        print(f"{api_url}\n{params}")
                page_data = res['query']['pages'][next(iter(res['query']['pages']))]
                if 'length' in page_data:
                    vv['languages'][lang_prefix]['length'] = page_data['length']
                else:
                    skipped.append((kk, lang_prefix))
    if skipped:
        for page, lang in skipped:
            print(f"[Skip] {page} in language {lang} (unavailable length)")
    save_to_file('data/cuisines_length.dat', cuisines)


def step4_preprocess_data_frame(create_full_df=False):
    """Create pandas DataFrames filtering out undesired data"""
    cuisines = load_from_file('data/cuisines_length.dat')

    # Set values (depending if dataframe/dataframe_full is to create)
    if create_full_df:
        threshold_min_voice_length = 0
        threshold_min_cuisines = 0
        threshold_min_languages = 0
        filename = 'data/table_dataframe_full.dat'
    else:
        threshold_min_voice_length = defs.THRESHOLD_MIN_VOICE_LENGTH
        threshold_min_cuisines = defs.THRESHOLD_MIN_CUISINES
        threshold_min_languages = defs.THRESHOLD_MIN_LANGUAGES
        filename = 'data/table_dataframe.dat'

    # Set pandas view options
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    # Find languages to consider
    languages = set()
    for kk, vv in cuisines.items():
        for lang in [*vv['languages'].keys()]:
            languages.add(lang)
    languages = [*languages]
    languages.sort()
    languages.insert(0, 'cuisine')

    # Create full table
    df_fulltable = pd.DataFrame(columns=languages)
    for kk, vv in tqdm(cuisines.items()):
        entry = {}
        for kk2, vv2 in vv['languages'].items():
            if 'length' in vv2 and kk2 in languages:
                entry[kk2] = vv2['length']
            # Add cuisine name (removing "cuisine")
            entry['Cuisine'] = kk.replace(" cuisine", "")
        df_fulltable = df_fulltable.append(entry, ignore_index=True)

    short_voices = []
    for (c_name, c_data) in df_fulltable.iteritems():
        if c_name != 'Cuisine':
            for entry in c_data.iteritems():
                if not pd.isna(entry[1]) and int(entry[1]) < threshold_min_voice_length:
                    short_voices.append((c_name, entry[0], entry[1]))

    for entry in short_voices:
        df_fulltable.at[entry[1], entry[0]] = np.nan

    # TODO:Fix: depending on the order different results are obtained
    # Keep all languages that have least THRESHOLD_MIN_CUISINES written
    df_fulltable.dropna(axis=1, thresh=threshold_min_cuisines, inplace=True)
    # Keep all cuisines that appears in at least THRESHOLD_MIN_LANGUAGES languages
    df_fulltable = df_fulltable[df_fulltable.isnull().sum(axis=1) < len(df_fulltable.columns) - threshold_min_languages]

    df_fulltable.reset_index(drop=True, inplace=True)
    df_fulltable.set_index('Cuisine', inplace=True)
    df_fulltable.columns.names = ['Wikipedia language']

    save_to_file(filename, df_fulltable)


# yapf: disable
STEPS = [step1_prepare_cuisines_data,
         step2_populate_other_languages,
         step3_fill_lengths,
         step4_preprocess_data_frame]
# yapf: enable


def get_wikimedia_languages_list():
    """Download and create a correlation dict from language prefixes to long language names"""
    wiki_languages = {}
    req = requests.get('https://meta.wikimedia.org/wiki/Table_of_Wikimedia_projects')
    soup = BeautifulSoup(req.text, features='html.parser')
    table = soup.find_all('table', class_='sortable')[0]
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue
        code, english_name, local_name = [td.text.strip() for td in tds[:3]]
        code = code.replace(':', '')
        wiki_languages[code] = {'eng_name': english_name, 'local_name': local_name}
    save_to_file('data/wiki_languages.dat', wiki_languages)


def main():
    if not Path('data/cuisines_raw.dat').exists():
        execute_steps(STEPS, [i for i in range(0, len(STEPS))])
    elif not Path('data/cuisines_langs.dat').exists():
        execute_steps(STEPS, [i for i in range(1, len(STEPS))])
    elif not Path('data/cuisines_length.dat').exists():
        execute_steps(STEPS, [i for i in range(2, len(STEPS))])
    elif not Path('data/table_dataframe.dat').exists():
        execute_steps(STEPS, [i for i in range(3, len(STEPS))])
    if not Path('data/table_dataframe_full.dat').exists():
        step4_preprocess_data_frame(create_full_df=True)
    if not Path('data/wiki_languages.dat').exists():
        get_wikimedia_languages_list()

    cc1 = load_from_file('data/cuisines_raw.dat')
    cc2 = load_from_file('data/cuisines_langs.dat')
    cc3 = load_from_file('data/cuisines_length.dat')
    wl = load_from_file('data/wiki_languages.dat')
    df = load_from_file('data/table_dataframe.dat')
    df_full = load_from_file('data/table_dataframe_full.dat')

    # Plot dataframe
    step5_create_plots(df, df_full)


if __name__ == '__main__':
    main()
