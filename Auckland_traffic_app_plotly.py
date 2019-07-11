# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 16:38:30 2019

@author: KML
"""

#
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
#import folium
#import branca
from datetime import datetime
from dateutil.relativedelta import relativedelta
#import plotly.plotly as py
import plotly.graph_objs as go
import config

mapbox_access_token = config.MAPBOX_KEY
layout_width = 700
layout_height = 300


app = dash.Dash(__name__)
server = app.server

df = pd.read_csv(r'data/merged_date.csv', parse_dates = ['count_date'])
df.set_index('count_date', inplace = True)
df.drop_duplicates(inplace = True)
df.sort_index(inplace = True)
df_original = df.copy()
df = df[df.index > '2010-12-01']  # for now set this restriction to limit resources
epoch = datetime.utcfromtimestamp(0)
def unix_time_millis(dt):
    return (dt - epoch).total_seconds() #* 1000.0

def get_marks_from_start_end(start, end):
    ''' Returns dict with one item per month
    {1440080188.1900003: '2015-08',
    '''
    result = []
    current = start
    while current <= end:
        result.append(current)
        current += relativedelta(months=1)
    return {unix_time_millis(m):(str(m.strftime('%Y-%m'))) for m in result}
min_date, max_date = unix_time_millis(pd.to_datetime(df.index.min())), unix_time_millis(pd.to_datetime(df.index.max()))

time_period_range = {'One month ahead':1,  
                     'Three months ahead':3, 'Six months ahead':6, 'One year ahead':12, 'To the most recent date':1000}
max_volume = df['adt'].max()

def filter_data(df, date_range_min_ = '2010-01-01', date_rage_max_ = '2020-01-01', selected_volumes = [np.nanpercentile(df['adt'], 90), df['adt'].max()], min_sampling_count = 1):
    col_ = 'adt'
    if min_sampling_count > 1:
        df = df[df['sampling_count'] >= min_sampling_count]
    df = df.loc[date_range_min_:date_rage_max_]
    df = df[(df[col_] > selected_volumes[0]) & (df[col_] < selected_volumes[1])]
    return df

def define_data(df):
    return [go.Scattermapbox(
            lat=df['latitude'],
            lon=df['longitude'],
            mode='markers',
            
            marker=go.scattermapbox.Marker(
                size=12,
                opacity = 0.5,
                color = df['adt'], 
                cmin = 0,
                cmax = max_volume,
                colorbar=dict(
                    title='Daily traffic count',
                ), 
#                https://github.com/plotly/plotly.js/blob/5bc25b490702e5ed61265207833dbd58e8ab27f1/src/components/colorscale/scales.js
                colorscale='Reds'
            ),
            text=df['road_name'],
        )]
def define_layout():
    return go.Layout(
#        autosize=True,
        title = '7-day daily average traffic count',
        width = layout_width,
        height = layout_height + 100,        
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0, 'pad':0},  # 
        hovermode='closest',
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            style = 'light',
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=-36.848461,
                lon=174.763336
            ),
            pitch=0,
            zoom=9
        ),
    )
    
sampling_count = df['sampling_count'].unique()
sampling_count.sort()

app.layout = html.Div([
    # First row, header
    html.Div([
        html.Div('', className = 'one column'),
        html.Div([
                html.H3('Auckland Traffic Visualization')
        ], className = 'five columns'),
    ], className = 'row'),
    # second row, traffic graph and control
    
    html.Div([
        html.Div('', className = 'one column'),
        ## first column
        html.Div([
            dcc.Graph(id='Auck_map',
#              figure = create_fig(df),
#              animate=True,
#                  style={'margin-top': '20'}
            )], className = 'five columns'),
#            html.P('Click on the marker to display historical traffic counts'),
        ## second column
        html.Div([
            html.P(id = 'dispaly_info'),
#            html.H6('Select traffic volume range:'),
            html.P(id = 'volume_slider_display'),
            dcc.RangeSlider(
                        id='volume_slider',
                        min=0,
                        max=df['adt'].max(),
                        step=1000,
                        value=[0, df['adt'].max()]
                    ),
            html.P(id = 'time_period_display'),
            dcc.Slider(
                    id = 'datetime_Slider',
                    updatemode = 'mouseup', #don't let it update till mouse released
                    min = min_date,
                    max = max_date,
                    value = unix_time_millis(pd.to_datetime(df.index.min())),
                    step = unix_time_millis(pd.to_datetime('20180601')) - unix_time_millis(pd.to_datetime('20180501')),
                    # add markers for key dates
                    marks=get_marks_from_start_end(pd.to_datetime(df.index.min()),
                                                   pd.to_datetime(df.index.max()))
                    ),
            html.P('Select period length:'),
            dcc.Dropdown(
                    id = 'time_period_dropdown',
                    options = [{'label': ind, 'value': value} for ind, value in time_period_range.items()],
                    value = 1000,
                    clearable = False
            ),                
            html.P('Filter by the number of historical traffic counts:'),
            dcc.Dropdown(
                    id = 'sampling_count_dropdown',
                    options = [{'label': value, 'value': value} for value in sampling_count],
                    value = 1,
                    clearable = False
            ),
            
            
        ], className = 'four columns'),        
#        ], className = 'five columns'), 
    ], className = 'row'),
    
    # third row
    html.Div([
        html.Div('', className = 'one column'),
        html.Div(dcc.Graph(id = 'traffic_count_histogram'), className = 'five columns'),
        html.Div(dcc.Graph(id = 'time_series_plot'), className = 'four columns')
    ], className = 'row')
        
], className = 'row')

@app.callback(
    dash.dependencies.Output('traffic_count_histogram', 'figure'),
    [dash.dependencies.Input('volume_slider', 'value'),
     dash.dependencies.Input('time_period_dropdown', 'value'), 
     dash.dependencies.Input('datetime_Slider', 'value'),
     dash.dependencies.Input('sampling_count_dropdown', 'value')     
     ])
def update_histogram(selected_volumes, selected_period, selected_date_value, min_sampling_count):
    selected_date = datetime.fromtimestamp(selected_date_value)
    selected_date_ub = selected_date + relativedelta(months = selected_period)
    df_sub = filter_data(df, selected_date.date(), selected_date_ub.date(), selected_volumes, min_sampling_count)
    data = [go.Histogram(x = df_sub['adt'])]
    layout = go.Layout(title = 'Daily average traffic volume histogram',
#                  margin = {"b": 0, "l": 0,"t": 0,"r": 0},  
                  height = layout_height + 60,
                  width = layout_width,
                  xaxis = dict(title = 'Traffic volume'),
                  yaxis = dict(title = 'Number of traffic records'))
    return {'data':data, 'layout': layout}
    
    

@app.callback(dash.dependencies.Output('time_period_display', 'children'),
              [dash.dependencies.Input('time_period_dropdown', 'value'), 
                 dash.dependencies.Input('datetime_Slider', 'value')])
def display_time_period(selected_period, selected_date_value):
    d = datetime.fromtimestamp(selected_date_value)
    d_ub = min(d + relativedelta(months = selected_period), pd.to_datetime(df.index.max()))
    return f"Selecting dates between {d.strftime('%Y-%m-%d')} to {d_ub.strftime('%Y-%m-%d')}"

@app.callback(dash.dependencies.Output('volume_slider_display', 'children'),
              [dash.dependencies.Input('volume_slider', 'value')])
def display_volume_slider_range(volumes):
    return f'Selecting traffic volume between {volumes[0]} and {volumes[1]}'

@app.callback(dash.dependencies.Output('dispaly_info', 'children'),
              [dash.dependencies.Input('volume_slider', 'value'),
                 dash.dependencies.Input('time_period_dropdown', 'value'), 
                 dash.dependencies.Input('datetime_Slider', 'value')
                 ])
def display_value(selected_volumes, selected_period, selected_date_value):
    d = datetime.fromtimestamp(selected_date_value)
    d_ub = min(d + relativedelta(months = selected_period), pd.to_datetime(df.index.max())) 
    return f"Displaying 7-day average daily traffic records collected from {d.strftime('%Y-%m-%d')} to {d_ub.strftime('%Y-%m-%d')} with traffic volume between {selected_volumes[0]} and {selected_volumes[1]}."

@app.callback(
    dash.dependencies.Output('Auck_map', 'figure'),
    [#dash.dependencies.Input('volume_dropdown', 'value'),
     dash.dependencies.Input('volume_slider', 'value'),
     dash.dependencies.Input('time_period_dropdown', 'value'), 
     dash.dependencies.Input('datetime_Slider', 'value'),
     dash.dependencies.Input('sampling_count_dropdown', 'value')     
     ])
def update_map(selected_volumes, selected_period, selected_date_value, min_sampling_count):
#    date_range_min = selected_date
    selected_date = datetime.fromtimestamp(selected_date_value)
    selected_date_ub = selected_date + relativedelta(months = selected_period)
#    create_fig(df, date_range_min_ = '2010-01-01', date_rage_max_ = '2020-01-01', selected_volumes = [np.nanpercentile(df['adt'], 90), df['adt'].max()]):
    df_sub = filter_data(df, selected_date.date(), selected_date_ub.date(), selected_volumes, min_sampling_count)
    data = define_data(df_sub)
    layout = define_layout()
    return {'data':data, 'layout':layout}  #m._repr_html_()

def filter_data_by_coord(df, lon, lat):
    return df[(df['longitude'] == lon) & (df['latitude'] == lat)]

@app.callback(
    dash.dependencies.Output('time_series_plot', 'figure'),
    [dash.dependencies.Input('Auck_map', 'clickData')])
def display_click_data(clickData):
    if not clickData:
        data = [go.Scatter(x = np.linspace(0, 1, 10), y = np.random.randn(10))]
        plot_title = "Click a marker to show historical traffic count"
    else:

        lon = clickData['points'][0]['lon']
        lat = clickData['points'][0]['lat']
        plot_title = f"Historical traffic counts for {clickData['points'][0]['text']}"
        road_name = clickData['points'][0]['text']
        df_sub = filter_data_by_coord(df_original, lon, lat)
        df_sub.sort_index(inplace = True)
        data = [go.Scatter(x = df_sub.index, y = df_sub['adt'], name = road_name)]
    layout = dict(title = plot_title,
                  margin = {"l": 50},  # "b": 30, "l": 50,"t": 0,"r": 100
                  height = layout_height + 60,
                  width = layout_width,
                  xaxis = dict(title = 'Date'),
                  yaxis = dict(title = 'Daily average traffoc count'),
              )
    return {'data':data, 'layout':layout}

if __name__ == '__main__':
    app.run_server(debug=False)