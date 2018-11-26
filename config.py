
from plotly import graph_objs as go

# unified plot design
layout_for_plots = go.Layout(
    paper_bgcolor='black',
    plot_bgcolor='black',
    xaxis=dict(
        titlefont=dict(
            size=18,
            color='white'
        ),
        showticklabels=True,
        tickfont=dict(
            size=14,
            color='white'),
        automargin=True),
    yaxis=dict(
        titlefont=dict(
            size=18,
            color='white'
        ),
        automargin=True,
        showticklabels=True,
        tickfont=dict(
            size=14,
            color='white'
        )),
    font=dict(
        size=22,
        color='white')
    )          
                
                
strings_to_exclude = [
     '<Medien ausgeschlossen>',   
     'Audio weggelassen',
     'Ende-zu-Ende-Verschlüsselung',
     'Media omitted',
     'Audio omitted',
]













