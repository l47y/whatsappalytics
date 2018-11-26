import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.figure_factory as ff
import plotly.graph_objs as go
import emoji
import matplotlib.pyplot as plt
from config import layout_for_plots, strings_to_exclude
from wordcloud import WordCloud
from stop_words import get_stop_words
import warnings
from copy import copy




class Whatsapp_Analytics():
    
    def __init__(self, path, languages=['german']):
        self.path = path
        self.df = self.whatsapp_to_df(self.path)
        tables = list()
        names = list()
        for name in np.unique(self.df['Written_by']):
            tables.append(self.df.loc[self.df['Written_by'] == name, :])
            names.append(name)
        self.tables = tables
        self.names = names
        self.languages = languages

        
    def whatsapp_to_df(self, path_of_whatsapp_text=None,
                       exclude = strings_to_exclude):
        '''
        Takes a whatsapp chat backup and cleanse it and makes a table with
        timestamp, written by, message columns. If the function is unable to
        detect the format of the given chat, an error raises. 
        
        Args:
        my_name -- My whatsapp name like it appears in the original file
        other_name -- Name of chat partner like it appears in original file
        path_of_whatsapp_text -- Path where to find the original text file
        '''

        with open(path_of_whatsapp_text) as file:
            chat = file.read().split('\n')[:-1]
       
        formats = {'iphone': '\[\d\d\.\d\d\.\d\d\,\ \d\d:\d\d:\d\d\] ',
                   'android': '\\d\\d\\.\\d\\d\\.\\d\\d, \\d\\d:\\d\\d - '}    
        timestamp_formats = {'iphone': '\d\d\.\d\d\.\d\d\,\ \d\d:\d\d:\d\d',
                             'android': '\\d\\d\\.\\d\\d\\.\\d\\d, \\d\\d:\\d\\d'}     
        timeconversion_formats = {'iphone': '%d.%m.%y, %H:%M:%S',
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
        
        format_ = format_consistency_check(chat[0:10])
        self.format = format_

        for string in exclude:
            chat = [message for message in chat if string not in message]
      
        writtenby = np.empty(len(chat), dtype='U24')
        regex = '(?<=' + formats[format_] + ')(.*?)(?=:)'
        for i, s in enumerate(chat):
            who = re.search(regex, s)
            if (bool(who)):
                writtenby[i] = who.group(0)
            else:
                writtenby[i] = 'Sender not detected'

        timestamps = list()
        messages = list() 
        where_not_possible = list()
        for i, s in enumerate(chat): 
            timestamp = re.search(timestamp_formats[format_], s)
            if (len(s) > 0) & (bool(timestamp)):
                timestamp = timestamp.group(0)
                timestamps.append(timestamp)
                s = re.sub(formats[format_], '', s)
                s = re.sub(writtenby[i] + ': ', '', s)
                messages.append(s)
            else: 
                # concat parts of messages split by newline into one message.
                # This happens when doing .split('/n') after reading the file
                messages[-1] = messages[-1] + ' ' + s 
                where_not_possible.append(i)
        writtenby = [by for k, by in enumerate(list(writtenby)) if k not in where_not_possible]  
        if 'Sender not detected' in np.unique(writtenby):
            warnings.warn('Not in every message a sender could be detected.')
        timestamps = pd.to_datetime(timestamps, 
                                    format = timeconversion_formats[format_])
        table = pd.DataFrame({'Timestamp': timestamps, 
                              'Written_by': writtenby, 
                              'Message': messages})
        table.dropna(inplace=True)
        table = table.loc[table['Written_by'] != 'Sender not detected']
        return table


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
  
    
    def plot_dist_of_message_size(self, words_or_chars='words', nb_mode=False):
        
        message_sizes = self.calc_message_sizes()
        layout = copy(layout_for_plots)
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
        for key in message_sizes.keys():
            hist = go.Histogram(x=message_sizes[key], name=key, xbins=bins)
            traces.append(hist)
    
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
        
        
    def show_summary_statistics(self):
        message_sizes = self.calc_message_sizes()
        resptimes = self.calc_respond_time()
        summaries = list()
        for name, table in zip(self.names, self.tables):
            stats = {}
            stats['Number messages sent'] = table.shape[0]
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
    
    
    def plot_dist_of_respondtimes(self, tail=False, nb_mode=False):
        
        resptimes = self.calc_respond_time()['All_messages']
        layout = copy(layout_for_plots)
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
        for key in resptimes.keys():
            hist = go.Histogram(x=resptimes[key], xbins=bins, name=key)
            traces.append(hist)

        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
        
    
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
    
    
    def onlypospart(self, x):
        x = np.array(x)
        return x[x >= 0]
              
    
    def plot_intraday_active_time(self, min_step=60, nb_mode=False):
        
        def convert(date):
            date = datetime(date.year, date.month, date.day, 
                            date.hour, min_step*(date.minute // min_step))
            return date.time()
        
        traces = list()
        for table in self.tables:
            table_copy = table.copy(deep=True)
            table_copy['Timestamp'] = table_copy['Timestamp'].apply(convert)
            name = table_copy['Written_by'].iloc[0]
            hist = go.Histogram(x=np.sort(table_copy['Timestamp']), 
                                name = name)
            traces.append(hist)
            del table_copy
 
        layout = copy(layout_for_plots)
        layout['title'] = 'Distribution of messages during the day'
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
        
    
    def plot_wordcloud(self, who='all'):
        
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
        wc = WordCloud(stopwords=stopwords, width=1500, height=1500,
                       max_words=400, scale=1)
        wc.generate(text)
        plt.figure(figsize=(16,12))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis("off")
        plt.title('Wordcloud of ' + who, fontdict=dict(size=24, color='white'))
        plt.tight_layout()
        plt.show()
   
    
    def plot_dist_of_weekdays(self, nb_mode=False):
         
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
            bar = go.Bar(x=grouped.index, y=grouped, name=self.names[i])
            traces.append(bar)
          
        layout = copy(layout_for_plots)
        layout['title'] = 'Distribution of sent messages over weekdays'
        layout['xaxis'] = {
            'categoryorder': 'array',
            'categoryarray': [x for _, x in sorted(zip(weekdays.keys(), 
                                                       weekdays.values()))]
        }
        fig = go.Figure(data=traces, layout=layout)
        if nb_mode:
            return fig
        plot(fig)
        
    
    def plot_most_used_emojis(self, nb_mode=False):
    
        freqs = list()
        names = list()
        for table in self.tables:
            smilies = self.extract_emojis(table['Message'])
            freqs.append(pd.Series(smilies).value_counts()[0:10])
            names.append(table['Written_by'].iloc[0])
            
        # the following is done to sort the emojis by sum of usage of all 
        # persons in the chat
        freqs = pd.concat(freqs, axis=1, sort=True).fillna(0)
        vec = np.zeros(freqs.shape[0])
        for i in range(freqs.shape[1]):
            vec += freqs.iloc[:, i]
            
        ind = np.flip(np.argsort(vec))
        freqs = freqs.iloc[ind.values, :]
        traces = list()
        for i in range(freqs.shape[1]):
            bar = go.Bar(x=freqs.index, y=freqs.iloc[:, i], name=names[i])
            traces.append(bar)
        layout = copy(layout_for_plots)
        layout['title'] = 'Most used emojis'
        fig = go.Figure(traces, layout)
        if nb_mode:
            return fig
        plot(fig)
        

    def plot_overall_participition(self, nb_mode=False):
        
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
            }
        pie2 = { 
            'values': perc_days,
            'labels': self.names,
            "domain": {"x": [.52, 1]},
            'hoverinfo':'label+percent+name',
            'hole': .4,
            'type': 'pie',
            'name': 'Percentage of days of participation',
            }

        layout = copy(layout_for_plots)
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
        fig = go.Figure(data=[pie1, pie2], layout=layout)
        if nb_mode:
            return fig
        plot(fig)


    def plot_chronology(self, nb_mode=False):
        
        traces = list()
        
        for i in range(len(self.names)):
            t = self.tables[i].copy(deep=True)
            t.Timestamp = [x.date() for x in t.Timestamp]
            grouped = t.groupby('Timestamp').size()
            scat = go.Scatter(x=grouped.index, y=grouped, mode='lines+markers', 
                              name=self.names[i])
            traces.append(scat)

        layout = copy(layout_for_plots)
        layout['title'] = 'Number of messages sent over time'
        fig = go.Figure(data=traces, layout=layout)
        if nb_mode:
            return fig
        plot(fig)

  #  def get_number_messages_da

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
        
    
    def whatsapp_df_to_qatable(whatsapp_df, my_name, other_name, answer_delay=24*60, 
                           between_messages_delay=2):
        '''
        
        - - - NOT USED YET - - -
        
        
        Takes a table produced by whatsapp_to_df in makes a table with two columns:
        The first one contains messages by the other persons and the second one
        contains my answers.
        
        Args:
        whatsapp_df -- result of whatsapp_to_df
        my_name -- see whatsapp_to_df
        other_name -- See whatsapp_to_df
        answer_delay -- (MINUTES) My message will only be considered as an answer if the time
            difference between my message and the last message of the other person
            does not exeed this parameter. It aims to avoid considering messages as an answer
            which actually dont belong to the same conversion anymore. 
        between_messages_delay -- (MINUTUS) Concatenates all messages which are within the
            time range of this parameter. This is because people tend to partition their answers
            in multiple single messages.
        '''
        
        last_messages = list()
        answers = list()
        nrows = whatsapp_df.shape[0]
        for i in range(1, nrows):
            if (whatsapp_df.Written_by[i] == my_name) & (whatsapp_df.Written_by[i - 1] == other_name):
                
                time_until_answer = whatsapp_df.Timestamp[i] - whatsapp_df.Timestamp[i - 1]
                if time_until_answer.total_seconds() > 60 * answer_delay:
                    next
                
                lm_past = whatsapp_df.Timestamp[i - 1] - timedelta(minutes=between_messages_delay)
                past_times = whatsapp_df.Timestamp[:i]
                connected_last_messages = ' '.join(whatsapp_df.Message[:(i)][past_times > lm_past])
                
                
                lm_future = whatsapp_df.Timestamp[i] + timedelta(minutes=between_messages_delay)
                future_times = whatsapp_df.Timestamp[(i):nrows]
                connected_answers = ' '.join(whatsapp_df.Message[(i):nrows][future_times < lm_future])
        
                last_messages.append(connected_last_messages)
                answers.append(connected_answers)
                
        return pd.DataFrame({'Last_message': last_messages, 
                             'Answer': answers})
            



