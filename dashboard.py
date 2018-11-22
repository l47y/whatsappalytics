import io
import base64
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from dash.dependencies import Input, Output, State
from whatsapp_analytics import whatsapp_analytics


# ~ STYLES ~

all_elements_style = {
    'margin': '8',
    'borderColor': 'blue',
    'textAlign': 'center'
}

main_style = {
    'textAlign': 'center'
}

path_style = {
    'width': '50%',
    'height': '30px',
    'lineHeight': '30px',
    'borderWidth': '2px',
    'borderColor': 'blue',
    'borderStyle': 'dashed',
    'borderRadius': '5px',
    'textAlign': 'center',
    'margin': '10px',
    'fontColor': 'white',
}

button_style = {
    'width': '10%',
    'height': '30px',
    'fontColor': 'white',
    'backgroundColor': 'black',
    'textAlign': 'center'
}

server = flask.Flask(__name__)
ext_styles = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, server=server, external_stylesheets=ext_styles)


app.layout = html.Div(style=main_style, children=[
    html.Div([
        html.Div(['Insert Path to Chat']),
        dcc.Input(
            id='path',
            type='text',
        ),
    ], style=all_elements_style),
    html.Div(children=[
        html.Button('Upload chat', id='upload'),
    ]),
    html.Div([
        html.Div(['What do you want to']),
        dcc.Dropdown(
            id='chooseplot',
            options=[
                {'label': 'Most used Emojis', 'value': 'Most used Emojis'},
                {'label': 'Distribution of Message Sizes', 'value': 'Distribution of Message Sizes'},
                {'label': 'Intraday Active Time', 'value': 'Intraday Active Time'},
                {'label': 'Distribution of Long Respond Times', 'value': 'Distribution of Long Respond Times'},
                {'label': 'Distribution of Short Respond Times', 'value': 'Distribution of Short Respond Times'},
            ],
            value='Most used Emojis'
        )
    ], style={**{'width': '25%'}, **all_elements_style}),
    html.Div(id='showplot'),
])


def process_chat(path, what):
    wa = whatsapp_analytics('Nicolas', 'Kevin Nürnberg', path=path)
    if (what == 'Most used Emojis'):
        figure = wa.plot_most_used_emojis(nb_mode=True)
    elif (what == 'Distribution of Message Sizes'):
        figure = wa.plot_dist_of_message_size(nb_mode=True)
    elif (what == 'Intraday Active Time'):
        figure = wa.plot_intraday_active_time(nb_mode=True)
    elif (what == 'Distribution of Long Respond Times'):
        figure = wa.plot_dist_of_respondtimes(tail=True, nb_mode=True)
    elif (what == 'Distribution of Short Respond Times'):
        figure = wa.plot_dist_of_respondtimes(tail=False, nb_mode=True)

    figure = {'data': figure.data, 'layout': figure.layout}
    return html.Div([
        html.Div(dcc.Graph(id='plot', figure=figure))
    ])


@app.callback(Output('showplot', 'children'),
              [Input('upload', 'n_clicks'),
               Input('chooseplot', 'value')],
              [State('path', 'value')])
def upload_chat(n_clicks, what, path):
    if path is not None:
        children = [
            process_chat(path, what)
        ]
        return children


if __name__ == '__main__':
    app.run_server(debug=True)


