import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_daq as daq
from PIL import Image
import os

# Load your data
df_radar = pd.read_csv("CleanedData/player_radar.csv")
df_stats = pd.read_csv("CleanedData/player_stats_cleaned.csv")

# Merge the datasets on the 'player' column without adding suffixes
merged_df = pd.merge(df_stats, df_radar, on='player', how='outer', suffixes=('', '_drop'))

# Drop columns with duplicate names from the second dataframe
df = merged_df.drop(merged_df.filter(regex='_drop$').columns, axis=1)

df_merged = df.copy()

# Calculate performance metrics
df_merged['passing_commulative_performance'] = (
        0.05 * df_merged['passes_completed'] +
        1.5 * df_merged['assists'] +
        1.5 * df_merged['assisted_shots'] +
        0.2 * df_merged['passes_into_final_third'] +
        0.4 * df_merged['passes_into_penalty_area'] +
        0.3 * df_merged['crosses_into_penalty_area'] +
        0.1 * df_merged['progressive_passes']
)

df_merged['shooting_commulative_performance'] = (
        3 * df_merged['goals'] +
        0.7 * df_merged['shots_on_target'] +
        0.6 * df_merged['shots'] +
        0.4 * df_merged['shots_free_kicks'] +
        df_merged['pens_made']
)

df_merged['defence_commulative_performance'] = (
        -0.2 * df_merged['dribbled_past'] -
        df_merged['errors'] +
        0.5 * df_merged['blocks'] +
        0.75 * df_merged['blocked_shots'] +
        0.75 * df_merged['blocked_passes'] +
        df_merged['tackles_interceptions'] +
        0.2 * df_merged['clearances']
)

df_merged['possession_commulative_performance'] = (
        0.05 * df_merged['touches'] +
        0.2 * df_merged['touches_att_3rd'] +
        0.5 * df_merged['touches_att_pen_area'] +
        1 * df_merged['dribbles_completed'] +
        0.1 * df_merged['progressive_passes_received'] +
        -0.2 * df_merged['miscontrols'] +
        -0.5 * df_merged['dispossessed']
)

df_merged['total_performance'] = (
        df_merged['passing_commulative_performance'] +
        df_merged['shooting_commulative_performance'] +
        df_merged['defence_commulative_performance'] +
        df_merged['possession_commulative_performance']
)

# Determine the best player based on total performance
best_player_overall = df_merged.loc[df_merged['total_performance'].idxmax()]
default_team = 'Argentina'  # Set to 'Argentina' to show Argentina players initially
default_highlighted_player = best_player_overall['player']

# Calculate the average performance metrics for all players
average_performance = df_merged[
    ['defence_commulative_performance', 'passing_commulative_performance', 'shooting_commulative_performance',
     'possession_commulative_performance']].mean()

# Resize the image
image_path = "CleanedData/other.png"
image = Image.open(image_path)
resized_image = image.resize((300, 300))  # Resize to 300x300 for better fit

# Save the resized image to the assets folder
assets_folder = "assets"
os.makedirs(assets_folder, exist_ok=True)
resized_image_path = os.path.join(assets_folder, "resized_other.png")
resized_image.save(resized_image_path)

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(
    style={'backgroundColor': '#2c3e50', 'minHeight': '100vh'},  # Dark background color for the entire page
    children=[
        # Component 1
        html.Div([
            dbc.Row([
                dbc.Col(html.Div([
                    html.Label('Select team:', style={'fontWeight': 'bold', 'color': '#ecf0f1'}),  # Light text color
                    dcc.Dropdown(
                        id='team-dropdown',
                        options=[{'label': team, 'value': team} for team in df_merged['team'].dropna().unique()],
                        placeholder="Select a team",
                        clearable=True,
                        value=default_team,  # Set the default to 'Argentina'
                        style={'width': '100%', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
                        # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=4),

                dbc.Col(html.Div([
                    html.Label('Select players:', style={'fontWeight': 'bold', 'color': '#ecf0f1'}),  # Light text color
                    dcc.Dropdown(
                        id='player-dropdown',
                        placeholder="Select players",
                        multi=True,
                        clearable=True,
                        value=[default_highlighted_player],  # Pre-select the best player
                        style={'width': '100%', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
                        # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=4),

                dbc.Col(html.Div([
                    html.Label('Select player to highlight:', style={'fontWeight': 'bold', 'color': '#ecf0f1'}),
                    # Light text color
                    dcc.Dropdown(
                        id='highlight-player-dropdown',
                        placeholder="Select a player to highlight",
                        clearable=True,
                        value=default_highlighted_player,  # Highlight the best player by default
                        style={'width': '100%', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
                        # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=4),
            ]),
            html.Div([
                dcc.Graph(
                    id='player-card',
                    style={
                        "height": "70vh",
                        "width": "40%",
                        "backgroundColor": "#2c3e50",
                        "padding": "10px"  # Optional: inner padding
                    }
                ),  # Dark background for player card container
                dcc.Graph(
                    id='radar-chart',
                    style={
                        "height": "70vh",
                        "width": "60%",
                        "backgroundColor": "white"  # Set the background of the radar chart to white
                    }
                )  # Dark background for radar chart container
            ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'space-between',
                      'backgroundColor': '#2c3e50'})  # Dark background for container
        ]),

        # Component 2
        html.Div([
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='team-dropdown-2',
                        options=[{'label': team, 'value': team} for team in df['team'].dropna().unique()],
                        multi=True,
                        placeholder="Filter by Team",
                        style={'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},  # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=3),

                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='position-dropdown',
                        options=[{'label': position, 'value': position} for position in
                                 df['position'].dropna().unique()],
                        multi=True,
                        placeholder="Filter by Position",
                        searchable=True,
                        style={'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},  # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=3),

                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='player-dropdown-2',
                        options=[{'label': player, 'value': player} for player in df['player'].dropna().unique()],
                        multi=True,
                        placeholder="Select Players",
                        clearable=True,
                        style={'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},  # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=3),
            ]),

            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='metric_x-dropdown',
                        options=[{'label': col, 'value': col} for col in df.columns[4:]], value='shots',
                        multi=False,
                        placeholder="Select a metric for x-axis",
                        clearable=True,
                        style={'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},  # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=3),

                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='metric_y-dropdown',
                        options=[{'label': col, 'value': col} for col in df.columns[4:]], value='xg',
                        multi=False,
                        placeholder="Select a metric for y-axis",
                        clearable=True,
                        style={'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},  # Dark background for dropdown
                        className='custom-dropdown'
                    )
                ], style={'margin': '10px'}), width=3),
            ]),

            dbc.Row([
                dbc.Col(dcc.Graph(id='scatter-plot', style={"backgroundColor": "#2c3e50"}), width=12),
                # Dark background for scatter plot container
            ]),

            dbc.Row([
                dbc.Col(html.Div(style={'position': 'relative'}, children=[
                    dcc.Graph(id='bar-chart', style={"backgroundColor": "#2c3e50"}),
                    # Dark background for bar chart container
                    html.Div([
                        daq.BooleanSwitch(
                            id='barmode-switch',
                            on=True,
                            label="Stacked/Grouped",
                            labelPosition="top",
                            style={'color': '#ecf0f1'}  # Light text color for switch label
                        )
                    ], style={
                        'position': 'absolute',
                        'top': '35px',
                        'right': '150px',
                        'zIndex': '1000',
                        'padding': '5px',
                        'borderRadius': '5px',
                        'backgroundColor': '#2c3e50'  # Dark background for switch container
                    })
                ]), width=12)
            ]),
        ], style={'backgroundColor': '#2c3e50'})  # Dark background for the whole second component container
    ]
)


@app.callback(
    Output('player-dropdown', 'options'),
    Output('player-dropdown', 'value'),
    Output('highlight-player-dropdown', 'value'),
    Input('team-dropdown', 'value')
)
def set_player_options(selected_team):
    if not selected_team:
        player_options = [{'label': player, 'value': player} for player in df_merged['player'].unique()]
        return player_options, [default_highlighted_player], default_highlighted_player
    filtered_df = df_merged[df_merged['team'] == selected_team]
    player_options = [{'label': player, 'value': player} for player in filtered_df['player'].unique()]
    best_player_team = filtered_df.loc[filtered_df['total_performance'].idxmax()]['player']
    return player_options, [option['value'] for option in player_options], best_player_team


@app.callback(
    Output('highlight-player-dropdown', 'options'),
    Input('player-dropdown', 'value')
)
def set_highlight_player_options(selected_players):
    if not selected_players:
        return []
    return [{'label': player, 'value': player} for player in selected_players]


@app.callback(
    Output('player-card', 'figure'),
    Input('team-dropdown', 'value'),
    Input('player-dropdown', 'value'),
    Input('highlight-player-dropdown', 'value')
)
def update_player_card(selected_team, selected_players, highlighted_player):
    if highlighted_player:
        best_player = df_merged[df_merged['player'] == highlighted_player].iloc[0]
        title = f'<b>Selected Player Info: <b>{best_player["player"]}'
    elif not selected_team or selected_team == 'No Team':
        if selected_players:
            filtered_df = df_merged[df_merged['player'].isin(selected_players)]
            best_player = filtered_df.loc[filtered_df['total_performance'].idxmax()]
            title = f'<b>Best Selected Players Info: <b>{best_player["player"]}'
        else:
            best_player = df_merged.loc[df_merged['total_performance'].idxmax()]
            title = f'<b>Tournament Best Player Info: <b>{best_player["player"]}'
    else:
        filtered_df = df_merged[df_merged['team'] == selected_team]
        if filtered_df.empty:
            return go.Figure()
        best_player = filtered_df.loc[filtered_df['total_performance'].idxmax()]
        title = f'<b>Best Player Info: <b>{best_player["player"]}'

    position_map = {
        'FW': 'Forward',
        'DF': 'Defence',
        'GK': 'Goalkeeper',
        'MF': 'Midfielder'
    }
    position_full = position_map.get(best_player['position'], best_player['position'])

    fig = go.Figure()
    spacing = 0.1
    annotations = []
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.1, y=0.6,
                            text='<b>Name       : </b>' + str(best_player['player']),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.1, y=0.6 - spacing,
                            text='<b>Position   : </b>' + position_full,
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.1, y=0.6 - 2 * spacing,
                            text='<b>Team       : </b>' + str(best_player['team']),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.1, y=0.6 - 3.2 * spacing,
                            text='<b>Club       : </b>' + str(best_player['club']),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.1, y=0.6 - 4.1 * spacing,
                            text='<b>Year of Birth : </b>' + str(best_player['birth_year']),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.7, y=0.72,
                            text='<b>Goals       : </b>' + str(best_player['goals']),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.7, y=0.7 - spacing,
                            text='<b>Assists     : </b>' + str(best_player['assists']),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.7, y=0.7 - 2 * spacing,
                            text='<b>Passing   : </b>' + str(round(best_player['passing_commulative_performance'], 2)),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.7, y=0.7 - 3 * spacing,
                            text='<b>Shooting  : </b>' + str(round(best_player['shooting_commulative_performance'], 2)),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.7, y=0.7 - 4.2 * spacing,
                            text='<b>Defense   : </b>' + str(round(best_player['defence_commulative_performance'], 2)),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))
    annotations.append(dict(xref='paper', yref='paper',
                            x=0.7, y=0.7 - 5.1 * spacing,
                            text='<b>Possession: </b>' + str(
                                round(best_player['possession_commulative_performance'], 2)),
                            font=dict(family='Arial', size=14, color='#ecf0f1'),  # White text color
                            showarrow=False))

    fig.update_layout(
        title=title,
        titlefont={'size': 24, 'color': '#ecf0f1'},  # Light text color
        font_family='San Serif',
        width=650, height=500,
        template="plotly_dark",  # Use dark theme
        showlegend=False,
        paper_bgcolor="#2c3e50",  # Dark background color for the player card
        plot_bgcolor="#34495e",  # Slightly lighter dark color for the plot area
        font=dict(color='#ecf0f1'),  # Light text color
        images=[dict(
            source=app.get_asset_url('resized_other.png'),
            xref="paper", yref="paper",
            x=0.11, y=1,
            sizex=0.25, sizey=0.35,
            xanchor="center", yanchor="top"
        )],
        legend=dict(orientation="v",
                    y=1,
                    yanchor="bottom",
                    x=1.0,
                    xanchor="right", ),
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(
                    color="#ecf0f1",  # Brighter border color
                    width=2
                )
            )
        ]
    )
    fig.update_layout(annotations=annotations)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    return fig


@app.callback(
    Output('radar-chart', 'figure'),
    [Input('team-dropdown', 'value'),
     Input('player-dropdown', 'value'),
     Input('highlight-player-dropdown', 'value')]
)
def update_radar_chart(selected_team, selected_players, highlighted_player):
    if not selected_players:
        return go.Figure()

    if selected_team == 'No Team' or not selected_team:
        filtered_df = df_merged
    else:
        filtered_df = df_merged[df_merged['team'] == selected_team]

    categories = [
        'defence_commulative_performance',
        'passing_commulative_performance',
        'shooting_commulative_performance',
        'possession_commulative_performance',
        'defence_commulative_performance'  # Repeat the first category to close the radar chart loop
    ]
    categories_labels = ['Defence', 'Passing', 'Shooting', 'Possession', 'Defence']

    fig = go.Figure()

    # Add the average performance line
    fig.add_trace(go.Scatterpolar(
        r=[average_performance[cat] for cat in categories],
        theta=categories_labels,
        name='Tournament Average',
        mode='lines',
        line_color='green',
        line_shape='spline',
        line_smoothing=0.8,
        opacity=0.8,
        line_width=2,
        hovertemplate='<b>%{theta}:%{r}<br></b><br>'
    ))

    for player in selected_players:
        player_data = filtered_df[filtered_df['player'] == player]
        if not player_data.empty:
            fig.add_trace(go.Scatterpolar(
                r=[player_data[cat].values[0] for cat in categories],
                theta=categories_labels,
                name=player,
                mode='lines',
                line_color='orange' if player == highlighted_player else 'black',
                line_shape='spline',
                line_smoothing=0.8,
                opacity=1 if player == highlighted_player else 0.6,
                line_width=3 if player == highlighted_player else 1,
                hovertemplate='<b>%{theta}:%{r}<br></b><br>'
            ))

    fig.update_layout(
        polar=dict(
            bgcolor='white',  # Set the background color of the circular area to white
            radialaxis=dict(
                visible=True,
                showticklabels=False,  # Hide tick labels
                showline=True,
                showgrid=True,
                gridcolor='#F2F2F2'
            ),
            angularaxis=dict(
                showticklabels=True,  # Hide tick labels
                showline=True,
                showgrid=True,
                gridcolor='#F2F2F2'
            )
        ),
        title=f'<b>Performance Metrics<b>',
        font=dict(size=15, color='white'),
        paper_bgcolor="#2c3e50",  # Dark background for the entire visual
        plot_bgcolor="#2c3e50"  # Dark background for the entire visual
    )

    return fig


@app.callback(
    [Output('metric_x-dropdown', 'options'),
     Output('metric_y-dropdown', 'options')],
    [Input('position-dropdown', 'value')]
)
def update_metric_dropdowns(selected_position):
    if selected_position:
        available_metrics = df[df['position'].isin(selected_position)].columns[4:].tolist()
        options = [{'label': metric, 'value': metric} for metric in available_metrics]
    else:
        options = [{'label': col, 'value': col} for col in df.columns[4:]]
    return options, options


@app.callback(
    Output('position-dropdown', 'options'),
    Input('team-dropdown-2', 'value')
)
def update_position_dropdown(selected_teams):
    filtered_df = df.copy()
    if selected_teams:
        filtered_df = filtered_df[filtered_df['team'].isin(selected_teams)]

    position_options = [{'label': position, 'value': position} for position in
                        filtered_df['position'].dropna().unique()]
    return position_options


@app.callback(
    Output('player-dropdown-2', 'options'),
    [Input('team-dropdown-2', 'value'),
     Input('position-dropdown', 'value')]
)
def update_player_dropdown(selected_teams, selected_positions):
    filtered_df = df.copy()
    if selected_teams:
        filtered_df = filtered_df[filtered_df['team'].isin(selected_teams)]
    if selected_positions:
        filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]

    player_options = [{'label': player, 'value': player} for player in filtered_df['player'].dropna().unique()]
    return player_options


@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('team-dropdown-2', 'value'),
     Input('position-dropdown', 'value'),
     Input('player-dropdown-2', 'value'),
     Input('metric_x-dropdown', 'value'),
     Input('metric_y-dropdown', 'value')]
)
def update_scatter_plot(selected_teams, selected_positions, selected_players, selected_metric_x, selected_metric_y):
    if not selected_metric_x or not selected_metric_y:
        return go.Figure(layout=go.Layout(
            title='Select metrics for x and y axes',
            titlefont={'color': '#ecf0f1'},
            paper_bgcolor='#2c3e50',
            plot_bgcolor='#34495e',
            font=dict(color='#ecf0f1')
        ))

    if selected_metric_x not in df.columns or selected_metric_y not in df.columns:
        return go.Figure(layout=go.Layout(
            title='Invalid metrics selected for x or y axis',
            titlefont={'color': '#ecf0f1'},
            paper_bgcolor='#2c3e50',
            plot_bgcolor='#34495e',
            font=dict(color='#ecf0f1')
        ))

    filtered_df = df.copy()
    if selected_teams:
        filtered_df = filtered_df[filtered_df['team'].isin(selected_teams)]
    if selected_positions:
        filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]

    color_map = {'All Players': 'lightblue'}
    colors = px.colors.qualitative.Set1
    if selected_players:
        for i, player in enumerate(selected_players):
            color_map[player] = colors[i % len(colors)]
    else:
        selected_players = ['All Players']

    filtered_df['color'] = filtered_df['player'].map(color_map).fillna('lightgrey')
    filtered_df['legend_group'] = filtered_df['player'].apply(lambda x: x if x in selected_players else 'All Players')

    fig = px.scatter(
        filtered_df,
        x=selected_metric_x,
        y=selected_metric_y,
        color='legend_group',
        color_discrete_map=color_map,
        hover_name='player',
        hover_data={
            'team': True,
            'position': True,
            selected_metric_x: True,
            selected_metric_y: True,
            'legend_group': False
        },
        title=f'{selected_metric_x} vs. {selected_metric_y}'
    )

    fig.update_traces(marker={'size': 20, 'opacity': 1.0})

    if selected_players and selected_players != ['All Players']:
        fig.for_each_trace(
            lambda trace: trace.update(marker={'opacity': 0.4}) if trace.name == 'All Players' else trace.update(
                marker={'opacity': 1.0}))

    fig.update_layout(
        margin={'l': 30, 'b': 30, 't': 40, 'r': 150},
        hovermode='closest',
        transition_duration=200,
        showlegend=bool(selected_players and selected_players != ['All Players']),
        legend=dict(yanchor="top", y=1, xanchor="left", x=1.02),
        paper_bgcolor="#2c3e50",  # Dark background color for the scatter plot
        plot_bgcolor="#34495e",  # Slightly lighter dark color for the plot area
        font=dict(color='#ecf0f1')  # Light text color
    )

    return fig


@app.callback(
    Output('player-dropdown-2', 'value'),
    [Input('scatter-plot', 'clickData'),
     Input('scatter-plot', 'selectedData')],
    [State('player-dropdown-2', 'value')]
)
def update_selected_players(clickData, selectedData, selected_players):
    if selected_players is None:
        selected_players = []

    # Handle clickData
    if clickData is not None:
        clicked_player = clickData['points'][0]['hovertext']
        if clicked_player in selected_players:
            selected_players.remove(clicked_player)
        else:
            selected_players.append(clicked_player)

    # Handle selectedData
    if selectedData is not None:
        for point in selectedData['points']:
            selected_player = point['hovertext']
            if selected_player not in selected_players:
                selected_players.append(selected_player)

    return selected_players


@app.callback(
    Output('bar-chart', 'figure'),
    [Input('team-dropdown-2', 'value'),
     Input('position-dropdown', 'value'),
     Input('player-dropdown-2', 'value'),
     Input('metric_x-dropdown', 'value'),
     Input('metric_y-dropdown', 'value'),
     Input('barmode-switch', 'on')]
)
def update_bar_chart(selected_teams, selected_positions, selected_players, selected_metric_x, selected_metric_y,
                     barmode):
    if not selected_players:
        return go.Figure(layout=go.Layout(
            title='Select players to see the bar chart',
            titlefont={'color': '#ecf0f1'},
            paper_bgcolor='#2c3e50',
            plot_bgcolor='#34495e',
            font=dict(color='#ecf0f1')
        ))

    if selected_metric_x not in df.columns or selected_metric_y not in df.columns:
        return go.Figure(layout=go.Layout(
            title='Invalid metrics selected for x or y axis',
            titlefont={'color': '#ecf0f1'},
            paper_bgcolor='#2c3e50',
            plot_bgcolor='#34495e',
            font=dict(color='#ecf0f1')
        ))

    filtered_df = df.copy()
    if selected_teams:
        filtered_df = filtered_df[filtered_df['team'].isin(selected_teams)]
    if selected_positions:
        filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]
    if selected_players:
        filtered_df = filtered_df[filtered_df['player'].isin(selected_players)]

    grouped_df = filtered_df.groupby('player')[[selected_metric_x, selected_metric_y]].sum().reset_index()
    grouped_df['total'] = grouped_df[selected_metric_x] + grouped_df[selected_metric_y]
    grouped_df = grouped_df.sort_values('total', ascending=False).drop(columns=['total'])

    melted_df = pd.melt(grouped_df, id_vars=['player'], value_vars=[selected_metric_x, selected_metric_y],
                        var_name='Metric', value_name='Value')

    fig = px.bar(
        melted_df,
        x='player',
        y='Value',
        color='Metric',
        title=f'{selected_metric_x} vs. {selected_metric_y}',
        barmode='group' if barmode else 'stack',
        text_auto=True,
    )

    fig.update_layout(
        margin={'l': 30, 'b': 30, 't': 40, 'r': 150},
        hovermode='closest',
        transition_duration=200,
        legend=dict(yanchor="top", y=1, xanchor="left", x=1.02),
        paper_bgcolor="#2c3e50",  # Dark background color for the bar chart
        plot_bgcolor="#34495e",  # Slightly lighter dark color for the plot area
        font=dict(color='#ecf0f1')  # Light text color
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8068)


