#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions for visualization and plotting
"""

import json
import pandas as pd
import plotly.graph_objects as go

from pathlib import Path

import defs
import ipdb


def get_country_flags():
    ipdb.set_trace()


def get_languages_names(language_prefixes):
    lang_lookup = json.load(open(Path('data/languages.json'), 'r'))
    lang_lookup_dict = {kk['code']: kk['name'] for kk in lang_lookup}
    language_names = []
    for lang in language_prefixes:
        if lang in lang_lookup_dict:
            language_names.append(f"{lang_lookup_dict[lang]} language")
        else:
            language_names.append(f"{lang} language")

    return language_names


def step5_plot_table(df):
    df = df.transpose()
    rows = []
    for idx, row in df.iterrows():
        rows.append(row.to_list())
    xlabels = df.columns.to_list()
    ylabels = df.index.to_list()

    # yapf: disable
    colorscale=[[0, "rgb(178, 233, 201)"],
                [0.1, "rgb(91, 207, 139)"],
                [0.2, "rgb(69, 201, 123)"],
                [0.3, "rgb(48, 164, 96)"],
                [0.4, "rgb(35, 121, 70)"],
                [0.5, "rgb(29, 99, 58)"],
                [0.6, "rgb(22, 77, 45)"],
                [0.7, "rgb(16, 55, 32)"],
                [0.8, "rgb(10, 33, 19)"],
                [0.9, "rgb(10, 33, 19)"],
                [1.0, "rgb(10, 33, 19)"]]
    # yapf: enable

    colorbar = dict(tick0=0, dtick=40000)

    if defs.REPLACE_LANGUAGES_ABBREVIATIONS:
        ylabels = get_languages_names(ylabels)
    if defs.ADD_CUISINES_COUNTRY_FLAG:
        xlabels = get_country_flags(xlabels)
        # TODO: Use https://en.wikipedia.org/wiki/List_of_adjectival_and_demonymic_forms_for_countries_and_nations
    if defs.ADD_CUISINE_TO_XLABELS:
        xlabels = [f"{kk} cuisine" for kk in xlabels]

    fig = go.Figure(data=go.Heatmap(x=xlabels, y=ylabels, z=rows, zmin=38, colorscale=colorscale, colorbar=colorbar))

    fig.update_layout(xaxis={
        'side': 'top',
        'tickangle': -60,
        'tickfont': {
            'size': 14
        }
    },
                      xaxis_showgrid=False,
                      yaxis_showgrid=False)

    ipdb.set_trace()
    fig.show()
