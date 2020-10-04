#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visualization and plotting
"""

import copy
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from pathlib import Path
from utils import get_flags_from_demonyms, get_languages_names, check_if_diagonal_value, load_from_file

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

def create_heatmap(df, ADD_FLAGS, DIAGONAL_MARKERS):
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
    if ADD_FLAGS:
        flags = get_flags_from_demonyms(xlabels)
        new_xlabels = []
        for nationality, flag in zip(xlabels, flags):
            if nationality != flag:
                new_xlabels.append(f"{flag} {nationality}")
            else:
                new_xlabels.append(f"{flag}")
        xlabels = new_xlabels

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
    if DIAGONAL_MARKERS:
        for n, (row, ylabel) in enumerate(zip(rows, ylabels)):
            for m, (val, xlabel) in enumerate(zip(row, xlabels)):
                if text := check_if_diagonal_value(xlabel, ylabel):
                    annotations.append(go.layout.Annotation(text=text,
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
    # yapf: enable
    return fig_hm


def create_sum_cuisines(df_full):
    fig_sum_cuisines = go.Figure(data=go.Bar(x=df_full.transpose().sum().index,
                                             y=df_full.transpose().sum().values,
                                             marker={
                                                 'color': df_full.transpose().sum().values,
                                                 'colorscale': defs.HEATMAP_COLORSCALE_BLUE
                                             }),
                                 layout=CUMULATIVE_GRAPHS_LAYOUT)
    return fig_sum_cuisines


def create_sum_languages(df_full):
    # yapf: disable
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
                                              marker={
                                                  'color': values,
                                                  'colorscale': defs.HEATMAP_COLORSCALE_BLUE
                                              }),
                                  layout=CUMULATIVE_GRAPHS_LAYOUT)
    return fig_sum_languages
    # yapf: enable


def step5_create_plots(df, df_full):
    pd.options.plotting.backend = 'plotly'

    # Replace language abbreviation with language name, sort the DataFrame
    df = df.transpose()
    df_full = df_full.drop(['cuisine'], axis=1)

    figures = {}

    # Create heatmap
    fig_hm = create_heatmap(df, defs.X_ADD_FLAGS, defs.MARKER_ON_DIAGONAL_CELLS)

    # (If enabled) create full heatmap
    if defs.PRODUCE_FULL_HEATMAP:
        fig_hm_full = create_heatmap(df_full.transpose(), False, False)
        figures['correlation_heatmap_full'] = fig_hm_full

    # Create statistics graphs
    fig_sum_cuisines = create_sum_cuisines(df_full)
    fig_sum_languages = create_sum_languages(df_full)

    # Create histogram
    if defs.PRODUCE_HISTOGRAM:
        fig_hist = df_full.hist()
        figures['historgram'] = fig_hist

    # yapf: disable
    figures.update({
        'correlation_heatmap': fig_hm,
        'cumulative_cuisines_length': fig_sum_cuisines,
        'cumulative_languages_length': fig_sum_languages
    })
    # yapf: enable

    if defs.STORE_STATISTICS:
        pd.set_option('display.float_format', '{:.0f}'.format)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_colwidth', None)

        # Cuisine leaderboard
        sum_data = df_full.transpose().sum().astype(int)
        leaderboard = sum_data.to_frame('length').sort_values('length', ascending=False)[0:30]
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
