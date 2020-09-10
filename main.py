#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to create a correlation matrix between Wikipedia cuisines pages
"""

import pandas as pd
import pickle
import re
import requests
import wikipedia as wiki

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen
from tqdm import tqdm

from defs import LANGS_TO_KEEP, LANGS_TO_SKIP

import time
import ipdb


def save(file, obj):
    with open(file, 'wb') as fp:
        pickle.dump(obj, fp)


def load(file):
    with open(file, 'rb') as fp:
        obj = pickle.load(fp)
    return obj


def step1_prepare_cuisines_data():
    cuisines_template_page = wiki.WikipediaPage('Template:Cuisines')
    soup = BeautifulSoup(cuisines_template_page.html(), features='html.parser')
    html_cuisines = soup.find(title='National dish').find_next('ul')
    cuisines_raw = dict()
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
                cuisines_raw[title] = unquote(href.replace('/wiki/', ''))
            elif 'mw-redirect' in cuisine.get('class'):
                print(f"Skipping '{cuisine.get('title')}' as it's only a redirect")
            else:
                print("Unhandled case")

    print("Creating cuisines dictionary...")
    for kk, vv in tqdm(cuisines_raw.items()):
        cuisines_raw[kk] = {'page': wiki.WikipediaPage(vv), 'languages': {}}

    save('data/cuisines_raw.dat', cuisines_raw)


def strip_url(text):
    result = re.search('://(.*)/wiki/', text)
    return result.group(1)


def step2_populate_other_languages():
    cuisines_raw = load('data/cuisines_raw.dat')

    wiki_url = 'https://en.wikipedia.org/w/api.php'
    params = {'action': 'query', 'prop': 'langlinks|info', 'llprop': 'url', 'lllimit': 'max', 'format': 'json'}
    print("Getting information from Wikipedia for every language...")
    for kk, vv in tqdm(cuisines_raw.items()):
        pageid = vv['page'].pageid
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
    save('data/cuisines.dat', cuisines_raw)


def step3_fill_lengths():
    cuisines = load('data/cuisines.dat')
    params = {'action': 'query', 'prop': 'info', 'format': 'json'}
    for kk, vv in tqdm(cuisines.items()):
        for lang_prefix, page in tqdm(vv['languages'].items()):
            #print(lang_prefix)
            #print(time.perf_counter())
            if lang_prefix != 'en' and lang_prefix not in LANGS_TO_SKIP:
                wiki_url = page['wiki_url']
                api_url = f'https://{wiki_url}/w/api.php'
                params['titles'] = page['title']
                print(f"\n{kk} - {lang_prefix}\n")
                with requests.Session() as session:
                    post = session.post(api_url, params)
                    if post.ok:
                        res = post.json()
                    else:
                        print("Issue in POST call")
                        print(f"{api_url}\n{params}")
                        ipdb.set_trace()

                    page_data = res['query']['pages'][next(iter(res['query']['pages']))]
                    if 'length' in page_data:
                        vv['languages'][lang_prefix]['length'] = page_data['length']
                    else:
                        print(f"No length for {kk} in language {lang_prefix}, skipped")
                try:
                    length = res['query']['pages'][next(iter(res['query']['pages']))]['length']
                    vv['languages'][lang_prefix]['length'] = length
                except (KeyError, json.decoder.JSONDecodeError) as error:
                    print(f"Error while getting length for {kk} in language {lang_prefix}")
    save('data/cuisines_length.dat', cuisines)


def get_wikimedia_languages_list():
    wiki_languages = {}
    url_wikimeida_projects = urlopen('https://meta.wikimedia.org/wiki/Table_of_Wikimedia_projects').read()
    soup = BeautifulSoup(url_wikimeida_projects, features='html.parser')
    table = soup.find_all('table', class_='sortable')[0]
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue
        code, english_name, local_name = [td.text.strip() for td in tds[:3]]
        code = code.replace(':', '')
        wiki_languages[code] = {'eng_name': english_name, 'local_name': local_name}
    save('data/wiki_languages.dat', wiki_languages)


def prepare_data_frame(cuisines):
    # Find which languages to consider
    languages = set()
    for kk, vv in cuisines.items():
        for lang in [*vv['languages'].keys()]:
            languages.add(lang)

    languages = [*languages]
    languages.sort()
    languages.insert(0, 'cuisine')
    df = pd.DataFrame(columns=languages)

    for kk, vv in cuisines.items():
        print(kk)
        df_entry = {kk2: vv2['length'] for kk2, vv2 in vv['languages'].items() if 'length' in vv2}
        df_entry['cuisine'] = kk
        df = df.append(df_entry, ignore_index=True)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    # Which languages have only few voices written?
    wl = load('data/wiki_languages.dat')
    df2 = pd.DataFrame(173 - df.isnull().sum())
    res = df2.to_dict()[0]
    del res['cuisine']
    res2 = {}
    for kk, vv in res.items():
        if kk in wl:
            res2[wl[kk]['eng_name']] = {'cuisines_pages': vv, 'lang_prefix': kk}
    res2_df = pd.DataFrame(res2, index=['cuisines_pages', 'lang_prefix'])
    res2_df = res2_df.transpose()
    res2_df = res2_df.sort_values('cuisines_pages', ascending=False)

    # Will keep first 50s entries
    languages_to_keep = res2_df['lang_prefix'][0:50].to_list()
    languages_to_keep.sort()
    languages_to_keep.insert(0, 'cuisine')

    df3 = pd.DataFrame(columns=languages_to_keep)
    for kk, vv in cuisines.items():
        print(f"{kk},{vv}")
        df_entry = {}
        for lang in languages_to_keep:
            if lang in vv['languages']:
                print(f"{lang}")
                try:
                    df_entry[lang] = vv['languages'][lang]['length']
                except KeyError:
                    print(f"KeyError processing {vv['languages'][lang]}")
        df_entry['cuisine'] = kk
        df3 = df3.append(df_entry, ignore_index=True)

    count_pages = {}
    for idx, row in df.iterrows():
        count_pages[row['cuisine']] = row.count() - 1

    res3_df = pd.DataFrame(count_pages, index=['count'])
    res3_df = res3_df.transpose()
    res3_df = res3_df.sort_values('count', ascending=False)

    ipdb.set_trace()


def create_correlation_lang_cuisines():
    cuisines = load('data/cuisines_length.dat')
    wl = load('data/wiki_languages.dat')
    wl_lookup = {vv['eng_name']: kk for kk, vv in wl.items()}
    wiki_cuisines_languages = {kk: '' for kk in [*cuisines.keys()]}
    for kk in wiki_cuisines_languages.keys():
        kk = kk.replace('Cuisine of the', '')
        kk = kk.replace('Cuisine of ', '')
        if kk.split()[0][-2:] == 'an':
            adjective = kk.split()[0]
            if adjective[:-2] in wl_lookup:
                wiki_cuisines_languages[kk] = wl_lookup[adjective[:-2]]
            elif adjective[:-3] in wl_lookup:
                wiki_cuisines_languages[kk] = wl_lookup[adjective[:-3]]
            elif adjective in wl_lookup:
                wiki_cuisines_languages[kk] = wl_lookup[adjective]

    ipdb.set_trace()
    print(len([kk for kk, vv in wiki_cuisines_languages.items() if vv]))


def main():
    if not Path('data/cuisines_raw.dat').exists():
        step1_prepare_cuisines_data()
        step2_populate_other_languages()
        step3_fill_lengths()
    elif not Path('data/cuisines.dat').exists():
        step2_populate_other_languages()
        step3_fill_lengths()
    elif not Path('data/cuisines_length.dat').exists():
        step3_fill_lengths()

    if not Path('data/wiki_languages.dat').exists():
        get_wikimedia_languages_list()
    #if not Path('data/wiki_cuisines_languages.dat').exists():
    #    create_correlation_lang_cuisines()

    cc1 = load('data/cuisines_raw.dat')
    cc2 = load('data/cuisines.dat')
    cc3 = load('data/cuisines_length.dat')
    wl = load('data/wiki_languages.dat')
    prepare_data_frame(cc3)


if __name__ == '__main__':
    main()
