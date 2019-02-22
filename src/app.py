import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from plotly.offline import plot
from config import background_col
from whatsapp_analytics import Whatsapp_Analytics
import os

# MAIN CONFIGURATION
##################################################################

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server)
app.css.append_css({'external_url': '/static/style.css'})
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
app.server.static_folder = 'static'  



# FURTHER CONFIGURATION
##################################################################

# Human readable plot methods and the python string which will be
# executed in the background when selecting one of them:
plot_method_translations = {
            'Chronology': 'plot_chronology(nb_mode=True)',
            'Message Size Distr.': 'plot_dist_of_message_size(nb_mode=True)',
            'Daily Active Time': 'plot_intraday_active_time(nb_mode=True)',
            'Distr. Over Weekdays': 'plot_dist_of_weekdays(nb_mode=True)', 
            'Most Used Emojis': 'plot_most_used_emojis(nb_mode=True)',
            'Overall Participition': 'plot_overall_participition(nb_mode=True)',
            'Distr. of Long Respondtimes': \
                'plot_dist_of_respondtimes(nb_mode=True, tail=True)',
            'Distr. of Short Respondtimes': \
                'plot_dist_of_respondtimes(nb_mode=True, tail=False)',
}


# STYLES STUFF
##################################################################

title_margin = '30px'
upper_right_margin = '100px'
upper_left_margin = '100px'
between_group_margin = '20px'
inner_group_margin = '5px'


parent_style = {
    'backgroundColor': background_col,
    #margin': '0',
    'text-align': 'center',
    'height': '100%'
}

path_style = {
    'color': 'white',
    'font-family': 'Ubuntu',
    'font-size': '20px',
    'font-weight': '300',
}


# APP LAYOUT
##################################################################

app.layout = html.Div(
    className='row',
    style={
        **parent_style,
        **{'height': '1200px'}
    },
    children=[
        html.Div(
            className='one column'
        ),
        html.Div(
            className='row',
            style={'height': title_margin}
        ),
        html.Div(
            className='two columns',
            style={'text-align': 'left'},
            children=[
                html.Div(
                    style={
                        **path_style,
                        **{'width': '800px'}
                    },
                    children=[html.H1('Analysis of Whatsapp Chats')]
                ),
                html.Div(
                    style={
                        'height': upper_left_margin,
                        'background-color': background_col
                    },
                ),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            style=path_style,
                            children=[
                                dcc.Input(
                                    id='path',
                                    type='text',
                                    placeholder='Insert Path to Chat...'
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(
                    className='row', 
                    style={'height': between_group_margin}
                ),
                html.Div(
                    className='row',
                    children=[
                         html.Div(
                            style={
                                **path_style,
                                **{'margin-left': '0px'}
                            },
                            children=[
                                'Choose a Language'
                            ]
                        ),
                    ]
                ),
                html.Div(
                    className='row',
                    style={'height': inner_group_margin},
                ),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            style={
                                **path_style,
                                **{'color': 'black'},
                            },
                            children=[
                                dcc.Dropdown(
                                    id='chooselanguage',
                                    options=[
                                        {'label': 'German', 'value': 'German'},
                                        {'label': 'English', 'value': 'English'},
                                        {'label': 'Spanish', 'value': 'Spanish'}
                                    ],
                                    value='German',
                                    multi=True,
                                )
                            ]
                        ),
                    ]
                ),
                html.Div(
                    className='row',
                    style={'height': between_group_margin}
                ),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            className='button button-primary',
                            children=[
                                html.Button(
                                    'Upload!', 
                                    id='upload',
                                    style={
                                        'border-width': '0px', 
                                        'font-size': '16px',
                                    }
                                ),
                            ]
                        )
                    ]
                ),
                html.Div(
                    className='row',
                    style={
                        'height': '60px',
                    },
                ),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            style={
                                **path_style,
                                **{'margin-left': '0px'}
                            },
                            children=[
                                'Choose a Plot'
                            ]
                        ),
                    ]
                ),
                html.Div(
                    className='row',
                    style={'height': inner_group_margin},
                ),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            style={
                                **path_style,
                                **{'color': 'black', 'width': '350px'},
                            },
                            children=[
                                dcc.Dropdown(
                                    id='chooseplot',
                                    options=[],
                                    placeholder='Please upload a Chat ...'
                                )
                            ]
                        ),
                    ]
                )
            ]
        ),
        html.Div(
            className='nine columns',
            children=[
                html.Div(
                    className='row',
                    style={'height': upper_right_margin}
                ),
                html.Div(
                    style = {
                        'height': '700px',
                    },
                    children = [
                        dcc.Graph(
                            id='showplot',
                            figure={
                                'data': [],
                                'layout': {
                                    'paper_bgcolor': background_col,
                                    'plot_bgcolor': background_col,
                                }
                            }
                        )
                    ]
                )
            ]
            
        )
    ]
)

# CALLBACKS
##################################################################

@app.callback(Output('chooseplot', 'options'),
              [Input('upload', 'n_clicks')],
              [State('path', 'value')])
def update_dropdown(n_clicks, path):
    if os.path.exists(str(path)):
        wa = Whatsapp_Analytics(path)
        for_dropdown = list()
        for key in plot_method_translations.keys():
            for_dropdown.append({'label': key, 'value': key})
        return for_dropdown


@app.callback(Output('chooseplot', 'value'),
              [Input('upload', 'n_clicks')],
              [State('path', 'value')])
def update_dropdown(n_clicks, path):
    if os.path.exists(str(path)):
        wa = Whatsapp_Analytics(path)
        for_dropdown = list()
        for key in plot_method_translations.keys():
            for_dropdown.append({'label': key, 'value': key})
        return for_dropdown[0]



@app.callback(Output('showplot', 'figure'),
             [Input('upload', 'n_clicks'),
              Input('chooseplot', 'value')],
             [State('path', 'value'),
              State('chooselanguage', 'value')])
def upload_chat(n_clicks, what, path, languages):
    if path is not None:
        wa = Whatsapp_Analytics(path, languages=languages)
        method = 'wa.' + plot_method_translations[what]
        fig = eval(method)
        return fig



# MAIN LOOP
##################################################################
if __name__ == '__main__':#
    app.run_server(debug=True)


#/home/nicolas/Escritorio/PyProjects/whatsappalytics/data/MuCoLe.txt
