#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visualization and plotting
"""

import copy
import emoji
import json
import pandas as pd
import plotly.graph_objects as go
import re

from pathlib import Path

import defs
import ipdb


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
    lang_lookup = json.load(open(Path('data/lookup_jsons/lookup_languages.json'), 'r'))
    lang_lookup_dict = {kk['code']: kk['name'] for kk in lang_lookup}
    language_names = []
    for lang in language_prefixes:
        try:
            language_names.append(f"{lang_lookup_dict[lang]}")
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
        print(f"Unknown key ({country})")
        return ''
    # From country to language
    country_languages_lookup = json.load(open(Path('data/lookup_jsons/lookup_countries_languages.json'), 'r'))
    country_languages_lookup_dict = {
        kk['country_name']: kk['lang_name']
        for kk in country_languages_lookup if 'lang_name' in kk
    }
    try:
        language = country_languages_lookup_dict[country]
    except KeyError:
        print(f"Unknown key ({country})")
        return ''

    if language.lower() == nn.lower():
        return '<b>●</b>'
    else:
        return ''


def step5_plot_table(df):
    # Set plotly as pandas backend
    pd.options.plotting.backend = 'plotly'

    df = df.transpose()
    # Replace language abbreviation with language name and sort the DataFrame
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
    replacements = {"Bosnia and Herzegovina": "Bosnian", "Kazakh": "Kazakhstani", "Nepalese": "Nepali"}
    new_xlabels = copy.deepcopy(xlabels)
    for idx, el in enumerate(xlabels):
        if el in replacements:
            new_xlabels[idx] = replacements[el]
    xlabels = new_xlabels

    # Apply modification if defined in defs.py
    if defs.Y_ADD_LANGUAGE:
        ylabels = [f"{kk} language" for kk in ylabels]
    if defs.X_ADD_FLAGS:
        flags = get_flags_from_demonyms(xlabels)
        new_xlabels = []
        for nationality, flag in zip(xlabels, flags):
            if nationality != flag:
                new_xlabels.append(f"{flag} {nationality}")
            else:
                new_xlabels.append(f"{flag}")
        xlabels = new_xlabels
    if defs.X_ADD_CUISINE:
        xlabels = [f"{kk} cuisine" for kk in xlabels]

    # Create figure and update the layout
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
    # Set annotations
    annotations=[{'x': 0.5,
                  'y': 1.15,
                  'showarrow': False,
                  'text': 'CUISINES',
                  'font': {'size': defs.AXIS_ANNOTATION_TEXT_SIZE},
                  'xref': 'paper',
                  'yref': 'paper'},
                 {'x': -0.07,
                  'y': 0.5,
                  'showarrow': False,
                  'text': 'LANGUAGES',
                  'font': {'size': defs.AXIS_ANNOTATION_TEXT_SIZE},
                  'textangle': -90,
                  'xref': 'paper',
                  'yref': 'paper'}]

    for n, (row, ylabel) in enumerate(zip(rows, ylabels)):
        for m, (val, xlabel) in enumerate(zip(row, xlabels)):
            annotations.append(go.layout.Annotation(text=check_if_diagonal_value(xlabel,ylabel),
                                                    font={'color': 'white', 'size': 14},
                                                    x=xlabels[m],
                                                    y=ylabels[n],
                                                    xref='x1',
                                                    yref='y1',
                                                    showarrow=False))
    fig_hm.update_layout(xaxis={'side': 'top',
                                'tickangle': -60,
                                'tickfont': {'size': 14}},
                         yaxis={'side': 'left',
                                'tickfont': {'size': 14}},
                         xaxis_showgrid=False,
                         yaxis_showgrid=False,
                         margin={'l': 120, 'r': 20, 't': 120, 'b': 20},
                         plot_bgcolor='rgb(245,245,250)',
                         annotations=annotations)
    # yapf: enable

    # Visualize the figure in the browser
    fig_hm.show()

    fig_sum_cuisines = go.Figure(data=go.Bar(
        y=df.transpose().sum().values,
        x=df.transpose().sum().index,
    ))
    fig_sum_cuisines.show()
    fig_sum_langs = go.Figure(data=go.Bar(
        y=df.sum().values,
        x=df.sum().index,
    ))
    fig_sum_langs.show()

    ipdb.set_trace()

    # Distribution figure
    fig = go.Figure()
    fig = df.hist()
    fig.show()
