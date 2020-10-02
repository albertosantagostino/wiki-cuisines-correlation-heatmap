#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visualization and plotting
"""

import copy
import emoji
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import re

from pathlib import Path
from utils import load_from_file

import defs

# yapf: disable
CUMULATIVE_GRAPHS_LAYOUT = {'xaxis': {'tickangle': 60,
                                     'tickfont': {'size': defs.TEXT_SIZE_LABELS-2}},
                            'yaxis': {'title': {'text': 'PAGES LENGTH SUM [characters]',
                                               'font': {'size': defs.TEXT_SIZE_AXIS_TITLE},
                                               'standoff': 40},
                                     'tickfont': {'size': defs.TEXT_SIZE_LABELS}, 'tick0': 0, 'dtick': 150000},
                            'bargap': 0,
                            'xaxis_showgrid': False,
                            'yaxis_showgrid': True,
                            'margin': {'l': 0, 'r': 0, 't': 0, 'b': 20},
                            'plot_bgcolor': 'rgb(245,245,250)'}
# yapf: disable

def get_flags_from_demonyms(country_demonyms):
    """Return a list of flags that correspond with the provided list of demonyms (adjectives)"""
    country_demonyms_lookup = json.load(open(Path('data/lookup_jsons/lookup_countries_demonyms.json'), 'r'))[0]
    flags = []
    for demonym in country_demonyms:
        try:
            country = country_demonyms_lookup[demonym].replace(' ', '_')
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
    lang_lookup_wl_dict = {kk: vv['eng_name'] for kk,vv in lang_lookup_wl.items()}
    for lang in language_prefixes:
        try:
            language_names.append(f"{lang_lookup_wl_dict[lang]}")
        except KeyError:
            language_names.append(f"{lang}")

    return language_names


def check_if_diagonal_value(mm, nn):
    mm = emoji.demojize(mm, delimiters=('<<', '>>'))
    #m = re.search('<<.*?>>', mm)
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


def step5_create_plots(df, df_full):
    pd.options.plotting.backend = 'plotly'

    # Replace language abbreviation with language name, sort the DataFrame
    df = df.transpose()
    if defs.Y_REPLACE_LANGUAGES_ABBREVIATIONS:
        languages = df.index.to_list()
        renaming_map = {lang: name for lang, name in zip(languages, get_languages_names(languages))}
        df.rename(index=renaming_map, inplace=True)
        df.sort_index(ascending=False, inplace=True)
    rows = []
    for idx, row in df.iterrows():
        rows.append(row.to_list())
    xlabels = df.columns.to_list()
    ylabels = df.index.to_list()

    # Handle demonyms exceptions manually
    new_xlabels = copy.deepcopy(xlabels)
    for idx, el in enumerate(xlabels):
        if el in defs.DEMONYMS_EXCEPTIONS:
            new_xlabels[idx] = defs.DEMONYMS_EXCEPTIONS[el]
    xlabels = new_xlabels

    # Add country flags to cuisines
    if defs.X_ADD_FLAGS:
        flags = get_flags_from_demonyms(xlabels)
        new_xlabels = []
        for nationality, flag in zip(xlabels, flags):
            if nationality != flag:
                new_xlabels.append(f"{flag} {nationality}")
            else:
                new_xlabels.append(f"{flag}")
        xlabels = new_xlabels

    # Create figures, add annotations
    # yapf: disable
    fig_hm = go.Figure(
        data=go.Heatmap(x=xlabels,
                        y=ylabels,
                        z=rows,
                        zmin=38,
                        colorscale=defs.HEATMAP_COLORSCALE_BLUE,
                        colorbar={'tick0': defs.THRESHOLD_MIN_VOICE_LENGTH,
                                  'dtick': 40000},
                        hovertemplate="Cuisine: %{x}<br>Wikipedia language: %{y}<br>Voice length: %{z}<extra></extra>"))
    annotations=[]
    if defs.MARKER_ON_DIAGONAL_CELLS:
        for n, (row, ylabel) in enumerate(zip(rows, ylabels)):
            for m, (val, xlabel) in enumerate(zip(row, xlabels)):
                annotations.append(go.layout.Annotation(text=check_if_diagonal_value(xlabel,ylabel),
                                                        font={'color': 'white', 'size': 16},
                                                        x=xlabels[m],
                                                        y=ylabels[n],
                                                        xref='x1',
                                                        yref='y1',
                                                        showarrow=False))
    fig_hm.update_layout(xaxis={'title': {'text': 'CUISINES','font': {'size': defs.TEXT_SIZE_AXIS_TITLE}},
                                'side': 'top',
                                'tickangle': -60,
                                'tickfont': {'size': defs.TEXT_SIZE_LABELS}},
                         yaxis={'title': {'text': 'WIKIPEDIA LANGUAGES','font': {'size': defs.TEXT_SIZE_AXIS_TITLE}},
                                'side': 'left',
                                'tickfont': {'size': defs.TEXT_SIZE_LABELS}},
                         xaxis_showgrid=False,
                         yaxis_showgrid=False,
                         margin={'l': 0, 'r': 0, 't': 0, 'b': 20},
                         plot_bgcolor='rgb(245,245,250)',
                         annotations=annotations)

    # Create statistics graphs
    df_full = df_full.drop(['cuisine'], axis=1)

    fig_sum_cuisines = go.Figure(data=go.Bar(x=df_full.transpose().sum().index,
                                             y=df_full.transpose().sum().values,
                                             marker={'color': df_full.transpose().sum().values,
                                                     'colorscale': defs.HEATMAP_COLORSCALE_BLUE}),
                                 layout=CUMULATIVE_GRAPHS_LAYOUT)

    languages = df_full.sum().index.to_list()
    values = df_full.sum().values
    if defs.X_LANGUAGES_GRAPH_REPLACE_LANGUAGES_ABBREVIATIONS:
        renaming_map = {lang: name for lang, name in zip(languages, get_languages_names(languages))}
        full_languages = []
        for lang_prefix in df_full.sum().index.to_list():
            full_languages.append(renaming_map[lang_prefix])
        sorted_data = sorted(zip(full_languages, values), key=lambda x: x[0])
        languages, values = [x[0] for x in sorted_data], [x[1] for x in sorted_data]

    fig_sum_languages = go.Figure(data=go.Bar(x=languages,
                                              y=values,
                                              marker={'color': values,
                                                      'colorscale': defs.HEATMAP_COLORSCALE_BLUE}),
                                  layout=CUMULATIVE_GRAPHS_LAYOUT)

    fig_hist = df_full.hist()

    figures = {'correlation_heatmap': fig_hm,
               'cumulative_cuisines_length': fig_sum_cuisines,
               'cumulative_languages_length': fig_sum_languages,
               'historgram_length': fig_hist}
    # yapf: enable

    if defs.STORE_STATISTICS:
        pd.set_option('display.float_format', '{:.0f}'.format)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_colwidth', None)
        # Cuisine leaderboard
        sum_data = df_full.transpose().sum().astype(int)
        leaderboard = sum_data.to_frame('length').sort_values('length', ascending=False)
        leaderboard.index = [
            f"{flag} {cuisine}"
            for flag, cuisine in zip(get_flags_from_demonyms(leaderboard.index), leaderboard.index.to_list())
        ]
        with open(Path(f'results/cuisines_leaderboard.md'), 'w') as fp:
            fp.write(leaderboard.to_markdown())
        # Top voices
        cc2 = load_from_file('data/cuisines_langs.dat')
        df_topvoices = pd.DataFrame(columns=['cuisine', 'language', 'length', 'url'])
        # yapf: disable
        for cuisine, row in df_full.iterrows():
            for language, length in row.to_frame('length').sort_values('length',ascending=False)[0:3]['length'].iteritems():
                if not np.isnan(length):
                    df_topvoices = df_topvoices.append({'cuisine': cuisine,
                                                        'language': language,
                                                        'length': length,},
                                                       ignore_index=True)
        # yapf: enable
        df_topvoices = df_topvoices.sort_values('length', ascending=False)[0:10]
        df_topvoices.reset_index(drop=True, inplace=True)
        urls = {}
        for idx, row in df_topvoices.iterrows():
            wikipage = cc2[f'{row["cuisine"]} cuisine']['languages'][row['language']]
            if row['language'] == 'en':
                wikiurl = 'en.wikipedia.org'
            else:
                wikiurl = wikipage['wiki_url']
            urls[idx] = f'[{row["cuisine"]} cuisine ({row["language"]})]' + '(https://' + wikiurl + '/wiki/' + wikipage[
                'title'].replace(' ', '_') + ')'
        for kk, vv in urls.items():
            df_topvoices['url'][kk] = vv
        df_topvoices['cuisine'] = [
            f"{flag} {cuisine}" for flag, cuisine in zip(get_flags_from_demonyms(df_topvoices['cuisine']),
                                                         df_topvoices['cuisine'].to_list())
        ]
        df_topvoices['language'] = get_languages_names(df_topvoices['language'])

        with open(Path(f'results/cuisines_top.md'), 'w') as fp:
            fp.write(df_topvoices.to_markdown())

    # Show plots in-browser
    if defs.SHOW_RESULTS:
        for fig_name, fig in figures.items():
            fig.show()

    # Store results (html/images)
    Path('results').mkdir(parents=True, exist_ok=True)
    for fig_name, fig in figures.items():
        if defs.STORE_HTML:
            with open(Path(f'results/{fig_name}.html'), 'w+') as fp:
                fp.write(fig.to_html())
        if defs.STORE_IMAGE:
            # Remove axes titles for image
            fig.update_layout(xaxis={'title': {'text': ''}}, yaxis={'title': {'text': ''}})
            with open(Path(f'results/{fig_name}.jpg'), 'wb+') as fp:
                fp.write(fig.to_image(format='jpg', width=1920, height=1080, scale=2.0))
