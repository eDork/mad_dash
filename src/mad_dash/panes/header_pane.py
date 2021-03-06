# -*- coding: utf-8 -*-
import datetime
import dash_core_components as dcc
import dash_html_components as html
import random

from mad_dash.simprod_db import spdb

url_input = dcc.Input(id = 'url_input',
                      value = 'mongodb-simprod.icecube.wisc.edu',
                      readonly = True,
                      size = 33,
                      type = 'text',
                      style = {'text-align': 'center'})

dbs = [n for n in spdb.database_names() if n != 'admin' and n!= 'local']
#db_dropdown = dcc.Dropdown(id = 'db_dropdown',
#                           options = [{'label': i, 'value': i} for i in dbs],
#                           value = 'simprod_histograms')
db_dropdown = dcc.Input(id = 'db_dropdown',
                        style = {'text-align': 'center'},
                        readonly = True,
                        size = 33,
                        type = 'text',
                        value = 'simprod_histograms')

db = spdb[db_dropdown.value]
collection_names = [n for n in db.collection_names()
                    if n not in ['system.indexes']]

coll_dropdown = dcc.Dropdown(id = 'coll_dropdown',
                             options = [{'label': i, 'value': i} for i in collection_names],
                             value = 'IceCube:2016:filtered:level2:CORSIKA-in-ice:20263')

coll = db[coll_dropdown.value]
histogram_names = [doc['name'] for doc in
                   db[coll_dropdown.value].find({'name' : {'$ne':'filelist'}})]

if 'filelist' in histogram_names:
    histogram_names.remove('filelist')

histograms = [coll.find_one({'name': name}) for name in histogram_names]
non_empty_histograms = [h for h in histograms if any(h['bin_values'])]
n_empty = len(histogram_names) - len(non_empty_histograms)
options = [{'label': i, 'value': i} for i in histogram_names]
default_histogram = random.choice(non_empty_histograms)
hist_dropdown = dcc.Dropdown(id = 'hist_dropdown',
                             options = options,
                             value = default_histogram['name'])

header_pane = html.Div([html.H1("Mad Dash"),
                        html.Hr(),
                        html.Div([html.Div([html.H3('Database URL'), url_input],
                                           className = 'two columns',
                                           style = {'width': '45%'}),
                                  html.Div([html.H3('Database Names'), db_dropdown],
                                           className = 'two columns',
                                           style = {'width': '45%'})],
                                 className = 'row'), 
                        html.Div([html.H3('Collections'), coll_dropdown]),
                        html.Div([html.H3('Histogram'),
                                  html.H4('There are %d histograms in this collection' % len(histogram_names),
                                          id = 'histogram-text'),
                                  html.H4('There are %d empty histograms' % n_empty,
                                          id = 'n-empty-histograms'),
                                  hist_dropdown,
                                  html.Div([html.Div(dcc.Graph(id='plot_linear_histogram'),
                                                     className = 'two columns',
                                                     style = {'width': '45%'}),
                                            html.Div(dcc.Graph(id='plot_log_histogram'),
                                                     className = 'two columns',
                                                     style = {'width': '45%'})],
                                           className = 'row')
                                  ]),
                        html.Hr()],
                       style = {'textAlign': 'center'})    

