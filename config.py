from plotly import graph_objs as go
import numpy as np


def convert_rgb_to_plotlycolor(rgb_vec):
    '''
    This function converts a rgb color vector into a string which will be 
    accpeted by plotly as a color.
    '''
    string = 'rgba(' + str(rgb_vec[0]) + ', ' + str(rgb_vec[1]) + ', ' + \
            str(rgb_vec[2]) + ', ' + str(1) + ')'
    return string


# Set the background grey tone
grey_tone = 50
background_col = convert_rgb_to_plotlycolor(np.repeat(grey_tone, 3))

# Define a unified plot format which will be used by every plot
layout_for_plots = go.Layout(
    paper_bgcolor=background_col,
    plot_bgcolor=background_col,
    xaxis=dict(
        titlefont=dict(
            size=18,
            color='white'
        ),
        showticklabels=True,
        tickfont=dict(
            size=14,
            color='white'),
        automargin=True
        ),
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
        size=20,
        color='white'),
    height=800,
 )          
                
   
# Some default strings which will be excluded later              
strings_to_exclude = [
     '<Medien ausgeschlossen>',   
     'Audio weggelassen',
     'Ende-zu-Ende-Verschlüsselung',
     'Media omitted',
     'Audio omitted',
     'Verpasster Sprachanruf',
     'Media omitida', 
     'Audio omitido',
     'extremo a extremo',
     'Verpasster Videoanruf',
     'Verpasster Sprachanruf',
     'Imagen omitida',
]


# A list of colors. Later randomly there will be picked x colors of this list
# where x stands for the number of chat participants. 
nice_colors = [
   [255, 0, 127], 
   [127, 0, 255],
   [0, 128, 255],
   [0, 255, 255],
   [0, 255, 128],
   [255, 255, 153],
   [255, 153, 204],
   [204, 153, 255],
   [153, 153, 255],
   [255, 153, 153],
   [255, 153, 255],
   [153, 255, 204]]
       
nice_colors = [convert_rgb_to_plotlycolor(c) for c in nice_colors]











