import re
import numpy as np
import pandas as pd
from datetime import datetime
from plotly.offline import plot
import plotly.graph_objs as go
from plotly import tools
import emoji
import matplotlib.pyplot as plt
from config import my_plot_themes, strings_to_exclude, nice_colors
from wordcloud import WordCloud
from stop_words import get_stop_words
from copy import copy
import random
import os
import plotly.io as pio



class Whatsapp_Analytics():
    '''
    Analysis object of a whatsapp chat backup. Make a backup in the menu of 
    a chat in your mobile and select "without media". Than place the resulting
    .txt file somewhere. There may be a lot of formats out there of this .txt 
    file which are not covered by this object. In the latter case, you will 
    receive a corresponding error. 
    
    Args of __init__:
    - path: Path where to find the original text file
    - languages: List of languages which are spoken in the chat. This
        will latebe used to exclude stopwords in the wordcloud.
    - exclude: A list of strings, where every message which contains one
        or more of the strings in exclude will be ignored. This is
        intended to be used to exclude the messages which are sent
        by whatsapp itself (for example: media omitted) or when 
        you want to ignore some kind of "private" messages.
    '''
    
    def __init__(self, path, languages=['german'], 
                 exclude = strings_to_exclude, pre_calculated_df=None, 
                 theme = 'dark'):
        self.path = path
        self.exclude = exclude
        if pre_calculated_df is not None:
            self.df = pre_calculated_df
        else:
            self.df = self.whatsapp_to_df(self.path, exclude=self.exclude)
        tables = list()
        names = list()
        for name in np.unique(self.df['Written_by']):
            tables.append(self.df.loc[self.df['Written_by'] == name, :])
            names.append(name)
        self.tables = tables
        self.names = names
        self.languages = languages
        
        ind = random.sample(range(len(nice_colors)), len(self.names))
        self.colors = [nice_colors[i] for i in ind]
        self.theme = theme
        if theme in my_plot_themes.keys():
            self.plot_theme = my_plot_themes[theme]
        else:
            raise ValueError('Only "light" and "dark" are valid theme parameters')
      
        
    def whatsapp_to_df(self, path_of_whatsapp_text=None,
                       exclude = strings_to_exclude):
        '''
        Takes a path to a whatsapp chat backup and produces a clean DataFrame.
        
        Args: see class docstring.
        
        Returns: DataFrame with three columns: 
            - Timestamp: Timestamp of message
            - Written_by: Name of chat member who has written the message
            - Message: Content of message
            
        Raises:
        ValueError: When format of that is not recognized 
        timestamp, written by, message columns. If the function is unable to
        detect the format of the given chat, an error raises. 
        '''

        with open(path_of_whatsapp_text) as file:
            chat = file.read().split('\n')[:-1]
       
        # Format detection:
        # First, a regex is used to seperate the message from the timestamp and
        # name. Second, the corresponding timestamp will be extracted with 
        # the timestamp-part of the first regex. Last, the correponding format
        # of the timestamp is specified to pass it later to pd.to_datetime
        
        formats = {'iphone': '\[\d\d\.\d\d\.\d\d\,\ \d\d:\d\d:\d\d\] ',
                   'iphone2': '\[\d+\/\d+\/\d\d \d+:\d+:\d+\] ',
                   'android': '\\d\\d\\.\\d\\d\\.\\d\\d, \\d\\d:\\d\\d - ',}
        
        timestamp_formats = {'iphone': '\d\d\.\d\d\.\d\d\,\ \d\d:\d\d:\d\d',
                             'iphone2': '\d+\/\d+\/\d\d \d+:\d+:\d+',
                             'android': '\\d\\d\\.\\d\\d\\.\\d\\d, \\d\\d:\\d\\d'}     
        
        timeconversion_formats = {'iphone': '%d.%m.%y, %H:%M:%S',
                                  'iphone2': '%d/%m/%y %H:%M:%S',
                                  'android': '%d.%m.%y, %H:%M'}
        
        # extract the format of a given message
        def extract_format(message_string):
            for f, string in formats.items():
                if bool(re.search(string, message_string)):
                    return(f)
                   
                    
        # checks if the format of the first x messages is equal 
        def format_consistency_check(messages):
            found_formats = list() 
            for i in range(len(messages)):
                
                # If newline in one message than no format will be found.
                # So here will be checked if the first char is a letter and 
                # if yes, the loop skips this. 
                if not bool(re.search('[A-Z, a-z]', messages[i][0])):
                    found_formats.append(extract_format(messages[i]))
            if any([len(np.unique(found_formats)) > 1,
                    len(np.unique(found_formats)) < 1]):
                raise ValueError('The provided chat format is not known yet.')
            return np.unique(found_formats)[0]  
        
        # Finally append the format attribute to the object
        format_ = format_consistency_check(chat[0:10])
        self.format = format_
        
        # Delete messages which contain some of the strings in exclude
        for string in exclude:
            chat = [message for message in chat if string not in message]
      
        # Initialize a list for every column
        timestamps = list()
        messages = list() 
        writtenby = list()
        
        for i, s in enumerate(chat): 
            timestamp = re.search(timestamp_formats[format_], s)
            if (len(s) > 0) & (bool(timestamp)):
                
                after_format = re.split(formats[format_], s)[1]
                
                # If the ":" not in a message than the message is from whatsapp
                # ifself like "xx has left the group"
                if ':' not in after_format:
                    continue
                else:
                    who = after_format.split(':')[0]
                    writtenby.append(who)
                
                timestamp = timestamp.group(0)
                timestamps.append(timestamp)
                s = re.sub(formats[format_], '', s)
                s = re.sub(who + ': ', '', s)
                messages.append(s)
            else: 
                # concat parts of messages split by newline into one message.
                # This happens when doing .split('/n') after reading the file
                messages[-1] = messages[-1] + ' ' + s 
        
        timestamps = pd.to_datetime(timestamps, 
                                    format = timeconversion_formats[format_])
        
        # Finally the table
        table = pd.DataFrame({'Timestamp': timestamps, 
                              'Written_by': writtenby, 
                              'Message': messages})
        table.dropna(inplace=True)
        table = table.loc[table['Written_by'] != 'Sender not detected']
        return table

    ########################################################################
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # PLOT SECTION ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ #
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~#
    ########################################################################
    
    def plot_dist_of_message_size(self, words_or_chars='words', nb_mode=False,
                                  only_trace=False):
        
        message_sizes = self.calc_message_sizes()
        layout = copy(self.plot_theme)
        if words_or_chars == 'words':
            message_sizes = message_sizes['Wordlengths']
            layout['title'] = 'Distribution of message lengths in words'
        else:
            message_sizes = message_sizes['Charlenghts']
            layout['title'] = 'Distribution of message lengths in characters'
          
        maxs = list()
        for key in message_sizes.keys():
            maxs.append(np.max(message_sizes[key]))
        xmax = np.max(maxs)
        bins = dict(start=0, end=xmax, size=xmax/30)    
        
        traces = list()
        for i, key in enumerate(message_sizes.keys()):
            hist = go.Histogram(x=message_sizes[key], name=key, xbins=bins,
                                marker=dict(color=self.colors[i]))
            traces.append(hist)
    
        if only_trace:
            return traces, layout
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
       
        
    @staticmethod
    def sum_two(x,y):
        return x+y
    
    def plot_dist_of_respondtimes(self, tail=False, nb_mode=False, 
                                  only_trace=False):
        
        resptimes = self.calc_respond_time()['All_messages']
        layout = copy(self.plot_theme)
        if tail:
            maxs = list()
            for key in resptimes.keys():
                maxs.append(np.max(resptimes[key]))
            xmax = np.max(maxs)
            bins =dict(start=30, size=xmax/30)
            layout['title'] = 'Distribution of long time respond time in minutes'
        else: 
            bins = dict(start=0, end=30, size=1)
            layout['title'] = 'Distribution of short time respond time in minutes'
        
        traces = list()
        for i, key in enumerate(resptimes.keys()):
            hist = go.Histogram(x=resptimes[key], xbins=bins, name=key,
                                marker=dict(color=self.colors[i]))
            traces.append(hist)
        
        if only_trace:
            return traces, layout
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
    
    
    def plot_intraday_active_time(self, min_step=60, nb_mode=False, 
                                  only_trace = False):
        
        def convert(date):
            date = datetime(date.year, date.month, date.day, 
                            date.hour, min_step*(date.minute // min_step))
            return date.time()
        
        traces = list()
        for i, table in enumerate(self.tables):
            table_copy = table.copy(deep=True)
            table_copy['Timestamp'] = table_copy['Timestamp'].apply(convert)
            name = table_copy['Written_by'].iloc[0]
            hist = go.Histogram(x=np.sort(table_copy['Timestamp']), 
                                name = name, 
                                marker=dict(color=self.colors[i]))
            traces.append(hist)
            del table_copy
 
        layout = copy(self.plot_theme)
        layout['title'] = 'Distribution of messages during the day'
        if only_trace:
            return traces, layout
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
        
    
    def plot_wordcloud(self, who='all', nb_mode=False):
        
        if who == 'all':
            df = self.df
        else:
            try:
                df = self.df.loc[self.df['Written_by'] == who, :]
            except ValueError:
                print('The name you entered does not occur in the chat.'
                      'Check .names attribute to see all possibe names')
                
        text = ' '.join(df['Message']).lower()
        stopwords = get_stop_words(self.languages[0])
        if len(self.languages) > 1:
            for i in range(1, len(self.languages)):
                stopwords.extend(get_stop_words(self.languages[i]))
        if self.theme == 'dark':
            background = 'black'
        elif self.theme == 'light':
            background = 'white'
        wc = WordCloud(stopwords=stopwords, width=1500, height=1500,
                       max_words=400, scale=1, background_color=background)
        wc.generate(text)
        plt.figure(figsize=(16,12))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis("off")
        plt.title('Wordcloud of ' + who, fontdict=dict(size=24, color='white'))
        plt.tight_layout()
        if nb_mode:
            return plt.gcf()
        else:
            plt.show()
   
    
    def plot_dist_of_weekdays(self, nb_mode=False, only_trace=False):
         
        traces = list()
        weekdays = {'1': 'Monday', 
                    '2': 'Tuesdays', 
                    '3': 'Wednesday', 
                    '4': 'Thursday', 
                    '5': 'Friday',
                    '6': 'Saturday', 
                    '7': 'Sunday'}
        for i in range(len(self.names)):
            t = self.tables[i].copy(deep=True)
            t['Timestamp'] = [x.isoweekday() for x in t['Timestamp']]
            t['Timestamp'] = t['Timestamp'].apply(str).replace(weekdays)
            grouped = t.groupby('Timestamp').size()
            bar = go.Bar(x=grouped.index, y=grouped, name=self.names[i],
                         marker=dict(color=self.colors[i]))
            traces.append(bar)
          
        layout = copy(self.plot_theme)
        layout['title'] = 'Distribution of sent messages over weekdays'
        layout['xaxis'] = {
            'categoryorder': 'array',
            'categoryarray': [x for _, x in sorted(zip(weekdays.keys(), 
                                                       weekdays.values()))]
        }
        if only_trace:
            return traces, layout
        fig = go.Figure(data=traces, layout=layout)
        if nb_mode:
            return fig
        plot(fig)
        
    
    def plot_most_used_emojis(self, nb_mode=False, only_trace=False):
    
        freqs = list()
        names = list()
        for table in self.tables:
            smilies = self.extract_emojis(table['Message'])
            freqs.append(pd.Series(smilies).value_counts())
            names.append(table['Written_by'].iloc[0])
            
        # the following is done to sort the emojis by sum of usage of all 
        # persons in the chat
        freqs = pd.concat(freqs, axis=1, sort=True).fillna(0)
        freqs["sum"] = freqs.apply(sum, axis=1)
        freqs.sort_values(by="sum", inplace=True, ascending=False)
        freqs = freqs.iloc[1:15, :]
        freqs.drop(["sum"], inplace=True, axis=1)
#        return(freqs)
#        vec = np.zeros(freqs.shape[0])
#        for i in range(freqs.shape[1]):
#            vec += freqs.iloc[:, i]
#            
#        ind = np.flip(np.argsort(vec))
#        freqs = freqs.iloc[ind.values, :]
        traces = list()
        for i in range(freqs.shape[1]):
            bar = go.Bar(x=freqs.index, y=freqs.iloc[:, i], name=names[i],
                         marker=dict(color=self.colors[i]))
            traces.append(bar)
        layout = copy(self.plot_theme)
        layout['title'] = 'Most used emojis'
        if only_trace:
            return traces, layout
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
        

    def plot_overall_participition(self, nb_mode=False, only_trace=False):
        
        days = self.df['Timestamp'].copy(deep=True)
        days = np.unique([x.date() for x in days])
        perc_mes = list()
        perc_days = list()
        for i in range(len(self.names)):
            tab = self.tables[i].copy(deep=True)
            perc_mes.append(tab.shape[0] / self.df.shape[0])
            days_person = [x.date() for x in tab['Timestamp']]
            perc_days.append(len(np.unique(days_person)) / len(days))
        
        pie1 = {
            'values': perc_mes,
            'labels': self.names,
            'domain': {'x': [0, .48]},
            'hoverinfo':'label+percent+name',
            'hole': .4,
            'type': 'pie',
            'name': 'Percentage of messages sent',
            'marker': dict(colors=self.colors)
            }
        pie2 = { 
            'values': perc_days,
            'labels': self.names,
            "domain": {"x": [.52, 1]},
            'hoverinfo':'label+percent+name',
            'hole': .4,
            'type': 'pie',
            'name': 'Percentage of days of participation',
            'marker': dict(colors=self.colors)
            }

        layout = copy(self.plot_theme)
        layout['title'] = 'Percentage of participation'
        layout['annotations'] = [
            {
                'font': {
                    'size': 17
                },
                'showarrow': False,
                'text': 'Messages',
                'x': 0.2130,
                'y': 0.5
            },
            {
                'font': {
                    'size': 17
                },
                'showarrow': False,
                'text': 'Days',
                'x': 0.775,
                'y': 0.5
            }
        ]
        if only_trace:
            return [pie1, pie2], layout
        fig = go.Figure(data=[pie1, pie2], layout=layout)
        if nb_mode:
            return fig
        plot(fig)


    def plot_chronology(self, nb_mode=False, only_trace=False):
        
        traces = list()
        
        for i in range(len(self.names)):
            t = self.tables[i].copy(deep=True)
            t.Timestamp = [x.date() for x in t.Timestamp]
            grouped = t.groupby('Timestamp').size()
            scat = go.Scatter(x=grouped.index, y=grouped, mode='lines+markers', 
                              name=self.names[i], 
                              marker=dict(color=self.colors[i]))
            traces.append(scat)

        layout = copy(self.plot_theme)
        layout['title'] = 'Number of messages sent over time'
        if only_trace:
            return traces, layout
        fig = go.Figure(data=traces, layout=layout)
        if nb_mode:
            return fig
        plot(fig)
    
    
    def plot_all_possible_plots(self, nb_mode=False):
        '''
        A really bad working work around for showing multiple plots in one
        html page. The layout doesn't adopt from the global layout correctly
        and some charts (at this moment the pie chart and wordcloud) can't be
        appended to the figure (although there might exist some workarounds).
        The intention of this is: In a GUI I want just to make one click and
        see everything. 
        '''
        
        # These plots don't work properly within a subplot and will be excluded
        not_working = ['plot_wordcloud', 'plot_overall_participition',
                       'plot_all_possible_plots']
        
        # Find all plot methods in this object which are not included in the
        # "not-working" ones.
        plots = [m for m in dir(self) if 'plot_' in m and m not in not_working]
        color_strings = self.colors
        
        traces_list = list()
        layout_list = list()
        titles = list()
        
        for i, method in enumerate(plots):
            traces, layout = getattr(self, method)(only_trace=True)
            traces_list.append(traces)
            layout_list.append(layout)
            titles.append(layout['title'])
            
        fig = tools.make_subplots(rows=len(plots), cols=1,
                                  subplot_titles = titles)
        
        for i, traces in enumerate(traces_list):
            if i == 0:
                sl = True
            else:
                sl = False
            for j, trace in enumerate(traces):
                trace['showlegend'] = sl
                trace['marker'] = dict(color = color_strings[j])
                fig.append_trace(trace, i + 1, 1)
                
        fig['layout'].update(
        font=self.plot_theme['font'],
        paper_bgcolor=self.plot_theme['paper_bgcolor'],
        plot_bgcolor=self.plot_theme['plot_bgcolor'], 
        height = 900*len(plots))
    
        # Some ugly and not working code for setting the layout to the global
        # plot layout. Still have to figure out how this works ....
        for i in range(len(plots)):
            xaxisstr = 'xaxis' + str(i + 1)
            yaxisstr = 'yaxis' + str(i + 1)
            fig['layout'][xaxisstr].update(
                    titlefont=self.plot_theme['xaxis']['titlefont'],
                    showticklabels=self.plot_theme['xaxis']['showticklabels'],
                    tickfont=self.plot_theme['xaxis']['tickfont'],
                    automargin=self.plot_theme['xaxis']['automargin'])
            fig['layout'][yaxisstr].update(
                    titlefont=self.plot_theme['yaxis']['titlefont'],
                    showticklabels=self.plot_theme['yaxis']['showticklabels'],
                    tickfont=self.plot_theme['yaxis']['tickfont'],
                    automargin=self.plot_theme['yaxis']['automargin'])

        if nb_mode:
            return fig
        plot(fig)
        
        
    def save_all_results(self, directory=os.getcwd() + "/images/", verbose=True):
        
        """
        Saves all possible plots to a directory. Even all statistics from 
        the show_summary_statistics function are saved as a single plot.
        
        Args:
        - directory: Target directory of the image files. Defaults to an 
          "image" folder within the working directory.
        """
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        not_working = ['plot_wordcloud',
               'plot_all_possible_plots', 'plot_theme']
        plots = [m for m in dir(self) if 'plot_' in m and m not in not_working]
        for method in plots:
            p = getattr(self, method)(nb_mode=True)
            pio.write_image(p, directory + method + ".jpg", format="jpg", 
                            height=1000, width=1000, scale=2)
        p = self.plot_dist_of_respondtimes(tail=True, nb_mode=True)
        pio.write_image(p, directory + "plot_dist_of_respondtimes_tail" + ".jpg", 
                        format="jpg", height=1000, width=1000, scale=2)
        if verbose:
            print("Standard plots ready.")
            
        plt.ioff()
        wc_all = self.plot_wordcloud(who="all", nb_mode=True)
        wc_all.savefig(directory + "wordcloud_all.jpg", dpi=200)
        for name in self.names:
            wc = self.plot_wordcloud(who=name, nb_mode=True)
            wc.savefig(directory + "wordcloud_" + name + ".jpg", dpi=200)
        plt.ion()
        if verbose:
            print("Wordclouds ready.")

        restable = self.show_summary_statistics()
        for stuff in restable.index:
            tmp = restable.loc[stuff, :]
            traces = list()
            for name, color in zip(self.names, self.colors):
                bar = go.Bar(x = [name], y=[tmp[name]], name=name, 
                             marker=dict(color=color))
                traces.append(bar)
            layout = copy(self.plot_theme)
            layout['title'] = stuff
            fig = go.Figure(traces, layout = layout)
            pio.write_image(fig, directory + stuff + ".jpg", format="jpg", 
                        height=1000, width=1000, scale=2)
        if verbose:
            print("Summary statistic plots ready.")

    ########################################################################
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # HELPER SECTION ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ #
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~#
    ########################################################################
    
    def calc_number_messages_per_day(self):
        num_mes_dict = {}
        for i, table in enumerate(self.tables):
            name = table['Written_by'].iloc[0]
            copy = table.copy(deep=True)
            copy['day'] = [stamp.date() for stamp in copy.Timestamp] 
            sizes = pd.Series(copy.groupby('day').size())
            num_mes_dict[name] = sizes
        return num_mes_dict
    
    
    def calc_message_sizes(self):
        worddict = {}
        chardict = {}
        for table in self.tables:
            name = table['Written_by'].iloc[0]
            wordlens = pd.Series([len(m.split(' ')) for m in table['Message']])
            charlens = pd.Series([len(m) for m in table['Message']])
            worddict[name] = wordlens
            chardict[name] = charlens
        return {'Wordlengths': worddict, 'Charlengths': chardict}
  
    def calc_respond_time(self):
        diffs = {}
        diffs_intraday = {}
        for name in self.names:
            diffs[name] = list()
            diffs_intraday[name] = list()
        
        for i in range(1, self.df.shape[0]):
            
            now = self.df['Timestamp'].iloc[i]
            last = self.df['Timestamp'].iloc[i - 1]
            now_pers = self.df['Written_by'].iloc[i]
            last_pers = self.df['Written_by'].iloc[i - 1]
            diff = now - last
            
            if (now_pers != last_pers): # so its considered to be a response
                diffs[now_pers].append(diff.total_seconds()/60)
                if (now.date() == last.date()): 
                    diffs_intraday[now_pers].append(diff.total_seconds()/60)
        
        return {'All_messages': diffs, 'Only_intraday': diffs_intraday}
     
    
    def meanround(self, x):
        return np.round(np.mean(x), decimals=3)
    
    
    def maxround(self, x):
        return np.round(np.max(x), decimals=3)
    
    
    def onlypospart(self, x):
        x = np.array(x)
        return x[x >= 0]
              
    
    def extract_emojis(self, messages):
        emojis_all = list()
        for message in messages:
            emojis = [c for c in message if c in emoji.UNICODE_EMOJI]
            emojis = [emoji.UNICODE_EMOJI[em] for em in emojis]
            emojis = [re.sub(':', '', emoji) for emoji in emojis]
            if len(emojis) > 0:
                emojis_all.extend(emojis)
        if len(emojis_all) > 0:
           return emojis_all
        else: 
            return ''

    ########################################################################
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # MISC SECTION ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ #
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~# 
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~#
    ########################################################################
        
    def show_summary_statistics(self):
        message_sizes = self.calc_message_sizes()
        resptimes = self.calc_respond_time()
        num_messages = self.calc_number_messages_per_day()

        summaries = list()
        for name, table in zip(self.names, self.tables):
            stats = {}
            stats['Number messages sent'] = table.shape[0]
            total_number_words = message_sizes['Wordlengths'][name].sum()
            total_number_chars = message_sizes['Charlengths'][name].sum()
            stats['Number words sent'] = total_number_words
            stats['Number characters sent'] = total_number_chars
            av_messages = self.meanround(num_messages[name])
            max_messages = self.maxround(num_messages[name])
            stats['Average number of messages per day'] = av_messages
            stats['Max number of messages sent in a day'] = max_messages
            av_wordlens = self.meanround(message_sizes['Wordlengths'][name])
            av_charlens = self.meanround(message_sizes['Charlengths'][name])
            stats['Average message size in words'] = av_wordlens
            stats['Average message size in characters'] = av_charlens
            av_resp_all = self.meanround(resptimes['All_messages'][name])
            av_resp_id = self.meanround(resptimes['Only_intraday'][name])
            stats['Average respond time for all messages (minutes)'] = av_resp_all
            stats['Average respond time for intraday messages (minutes)'] = av_resp_id
            series = pd.Series(np.fromiter(stats.values(), dtype='float64'))
            series.index = stats.keys()
            summaries.append(series)
        
        restable = pd.concat(summaries, axis=1, sort=False)
        restable.columns = self.names
        
        return restable
    
    
path = '/home/nicolas/Escritorio/PyProjects/whatsappalytics/data/PatrickNazli.txt'
languages = ['german', 'english'] 
wa = Whatsapp_Analytics(path, theme="dark", languages=languages,
                            exclude=strings_to_exclude)
x = wa.plot_most_used_emojis(nb_mode=True)
    