import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.figure_factory as ff
import plotly.graph_objs as go
import emoji
import matplotlib.pyplot as plt
from config import layout_for_plots
from wordcloud import WordCloud
from stop_words import get_stop_words




class whatsapp_analytics():
    
    def __init__(self, my_name, other_name, path=None, text=None,
                 languages=['german']):
        self.my_name = my_name
        self.other_name = other_name
        if text != None:
            self.df = self.whatsapp_to_df(self.my_name, self.other_name,
                                          whatsapp_text=text)
        else:  
            self.path = path
            self.df = self.whatsapp_to_df(self.my_name, self.other_name, 
                                          self.path)
        self.my_table = self.df.loc[self.df['Written_by'] == my_name, :]
        self.other_table = self.df.loc[self.df['Written_by'] == other_name, :]
        self.languages = languages

        
    def replace_german_umlaute(text):
        umlaute_dict = {
            '\\xc3\\xa4': 'ae',  
            '\\xc3\\xb6': 'oe',  
            '\\xc3\\xbc': 'ue', 
            '\\xc3\\x84': 'Ae',  
            '\\xc3\\x96': 'Oe', 
            '\\xc3\\x9c': 'Ue', 
            '\\xc3\\x9f': 'ss',
        }
        for k in umlaute_dict.keys():
            text = text.replace(k, umlaute_dict[k])
        return text
        
        
    def whatsapp_to_df(self, my_name, other_name, path_of_whatsapp_text=None,
                       whatsapp_text=None, 
                       no_media_string = '<Medien ausgeschlossen>'):
        '''
        Takes a whatsapp chat backup and cleanse it and makes a table with
        timestamp, written by, message columns
        
        Args:
        my_name -- My whatsapp name like it appears in the original file
        other_name -- Name of chat partner like it appears in original file
        path_of_whatsapp_text -- Path where to find the original text file
        '''
        
        if whatsapp_text != None:
            chat = whatsapp_text.split('/n')[:-1]
        else:
            with open(path_of_whatsapp_text) as file:
                chat = file.read().split('\n')[:-1]
       
        chat = [message for message in chat if no_media_string not in message]
        where_my_name = [my_name in s for s in chat]
        where_other_name = [not b for b in where_my_name]
        writtenby = np.empty(len(chat), dtype='U24')
        writtenby[where_my_name] = my_name
        writtenby[where_other_name] = other_name
        
        timestamps = list()
        messages = list() 
    
        where_not_possible = list()
    
        for i, s in enumerate(chat): 
            timestamp = re.search('\\d\\d\\.\\d\\d\\.\\d\\d, \\d\\d:\\d\\d', s)
            if (len(s) > 0) & (bool(timestamp)):
                timestamp = timestamp.group(0)
                timestamps.append(timestamp)
                s = re.sub('\\d\\d\\.\\d\\d\\.\\d\\d, \\d\\d:\\d\\d - ', '', s)
                s = re.sub(writtenby[i] + ': ', '', s)
                messages.append(s)
            else: 
                where_not_possible.append(i)
        writtenby = [by for k, by in enumerate(list(writtenby)) if k not in where_not_possible]        
        table = pd.DataFrame({'Timestamp': pd.to_datetime(timestamps, format='%d.%m.%y, %H:%M'), 
                              'Written_by': writtenby, 
                              'Message': messages})
        table.dropna(inplace=True)
        return table

    def calc_average_message_size(self, average=True):
        my_charlens = [len(m) for m in self.my_table['Message']]
        other_charlens = [len(m) for m in self.other_table['Message']]
        my_wordlens = [len(m.split(' ')) for m in self.my_table['Message']]
        other_wordlens = [len(m.split(' ')) for m in self.other_table['Message']]
        
        resdict = {}
        if average:
            resdict[self.my_name + '_charlen'] = self.meanround(my_charlens)
            resdict[self.other_name + '_charlen'] = self.meanround(other_charlens)
            resdict[self.my_name + '_wordlen'] = self.meanround(my_wordlens)
            resdict[self.other_name + '_wordlen'] = self.meanround(other_wordlens)
        else:
            resdict[self.my_name + '_charlen'] = my_charlens
            resdict[self.other_name + '_charlen'] = other_charlens
            resdict[self.my_name + '_wordlen'] = my_wordlens
            resdict[self.other_name + '_wordlen'] = other_wordlens
        
        return resdict
    
    
    def plot_dist_of_message_size(self, words=False, nb_mode=False):
        
        messages_sizes = self.calc_average_message_size(average=False)
        layout = layout_for_plots
        if words:
            my_sizes = messages_sizes[self.my_name + '_wordlen']
            other_sizes = messages_sizes[self.other_name + '_wordlen']
            layout['title'] = 'Distribution of message lengths in words'
        else:
            my_sizes = messages_sizes[self.my_name + '_charlen']
            other_sizes = messages_sizes[self.other_name + '_charlen']
            layout['title'] = 'Distribution of message lengths in characters'
        xmax = np.max([np.max(my_sizes), np.max(other_sizes)])
        bins = dict(start=0, end=xmax, size=xmax/30)
        trace = [go.Histogram(x=my_sizes, name=self.my_name, xbins=bins),
                 go.Histogram(x=other_sizes, name=self.other_name, xbins=bins)]
        fig = go.Figure(trace, layout)
        if nb_mode:
            return fig
        plot(fig)
        
        
    def show_summary_statistics(self):
        my_stuff = {}
        other_stuff = {}
        sizes_dict = self.calc_average_message_size()
        resptimes_dict = self.calc_average_respond_time()
        my_stuff['Messages send'] = self.my_table.shape[0]
        other_stuff['Messages send'] = self.other_table.shape[0]
        my_stuff['Average message size in words'] = \
            sizes_dict[self.my_name + '_wordlen']
        other_stuff['Average message size in words'] = \
            sizes_dict[self.other_name + '_wordlen']
        my_stuff['Average message size in characters'] = \
            sizes_dict[self.my_name + '_charlen']
        other_stuff['Average message size in characters'] = \
            sizes_dict[self.other_name + '_charlen']
        my_stuff['Average respond time for all messages (minutes)'] = \
            resptimes_dict[self.my_name]
        other_stuff['Average respond time for all messages (minutes)'] = \
            resptimes_dict[self.other_name]
        my_stuff['Average respond time for intraday messages (minutes)'] = \
            resptimes_dict[self.my_name + '_intraday']
        other_stuff['Average respond time for intraday messages (minutes)'] = \
            resptimes_dict[self.other_name + '_intraday']
        table = pd.DataFrame({'a': np.fromiter(my_stuff.values(), dtype='float64'), 
                              'b': np.fromiter(other_stuff.values(), dtype='float64')})
        table.columns = [self.my_name, self.other_name]
        table.index = my_stuff.keys()
        self.summary_stats = table
        return table
    
    def plot_dist_of_respondtimes(self, tail=False, nb_mode=False):
        resptimes = self.calc_average_respond_time(average=False)
        my_times = resptimes[self.my_name]
        other_times = resptimes[self.other_name]
        
        layout = layout_for_plots
        
        if tail:
            xmax = np.max([np.max(my_times), np.max(other_times)])
            bins =dict(start=30, size=xmax/30)
            layout['title'] = 'Distribution of long time respond time in minutes'
        else:
            xmax = np.max([np.max(my_times), np.max(other_times)])
            bins = dict(start=0, end=30, size=1)
            layout['title'] = 'Distribution of short time respond time in minutes'
        my_hist = go.Histogram(x=my_times, xbins=bins, name=self.my_name)
        other_hist =go.Histogram(x=other_times, xbins=bins, name=self.other_name)
        trace = [my_hist, other_hist]
        fig = go.Figure(trace, layout)
        if nb_mode:
            return fig
        plot(fig)
        
    
    def calc_average_respond_time(self, average=True):
        
        my_diffs = list()
        other_diffs = list()
        my_diffs_intraday = list()
        other_diffs_intraday = list()
        
        for i in range(1, self.df.shape[0]):
            
            now = self.df['Timestamp'][i]
            last = self.df['Timestamp'][i - 1]
            now_pers = self.df['Written_by'][i]
            last_pers = self.df['Written_by'][i - 1]
            diff = now - last
            
            if (now_pers == self.my_name) & (last_pers == self.other_name):
                my_diffs.append(diff.total_seconds()/60)
                if (now.date() == last.date()):
                    my_diffs_intraday.append(diff.total_seconds()/60)
            if (now_pers == self.other_name) & (last_pers == self.my_name):
                other_diffs.append(diff.total_seconds()/60)
                if (now.date() == last.date()):
                    other_diffs_intraday.append(diff.total_seconds()/60)
      
        resdict = {}
        if average:
            resdict[self.my_name] = self.meanround(my_diffs)
            resdict[self.other_name] = self.meanround(other_diffs)
            resdict[self.my_name + '_intraday'] = self.meanround(my_diffs_intraday)
            resdict[self.other_name + '_intraday'] = self.meanround(other_diffs_intraday)
        else:
            resdict[self.my_name] = self.onlypospart(my_diffs)
            resdict[self.other_name] = self.onlypospart(other_diffs)
            resdict[self.my_name + '_intraday'] = self.onlypospart(my_diffs_intraday)
            resdict[self.other_name + '_intraday'] = self.onlypospart(other_diffs_intraday)
        
        return resdict
          
    
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
       
        self.my_table['Timestamp_tmp'] = self.my_table['Timestamp'].apply(convert)
        self.other_table['Timestamp_tmp'] = self.other_table['Timestamp'].apply(convert)
        
        my_times = np.sort(self.my_table['Timestamp_tmp'])
        other_times = np.sort(self.other_table['Timestamp_tmp'])
        trace = [go.Histogram(x=my_times, name=self.my_name), 
                 go.Histogram(x=other_times, name=self.other_name)]
        layout = layout_for_plots
        layout['title'] = 'Distribution of messages during the day'
        fig = go.Figure(trace, layout)
        if nb_mode:
            return fig
        plot(fig)
        self.my_table.drop(['Timestamp_tmp'], axis=1, inplace=True)
        self.other_table.drop(['Timestamp_tmp'], axis=1, inplace=True)
        
    
    def plot_wordcloud(self, who='my_name'):
        
        if (who == self.my_name) or (who == 'my_name'):
            df = self.my_table
        else:
            df = self.other_table
        
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
   
    
    def plot_most_used_emojis(self, nb_mode=False):
    
        
        my_smilies = self.extract_emojis(self.my_table['Message'])
        my_freq = pd.Series(my_smilies).value_counts()[0:10]
        
        other_smilies = self.extract_emojis(self.other_table['Message'])
        other_freq = pd.Series(other_smilies).value_counts()[0:10]
        
        freq = pd.concat([my_freq, other_freq], axis=1).fillna(0)
        ind = np.flip(np.argsort(freq.iloc[:, 0] + freq.iloc[:, 1]))
        freq = freq.iloc[ind.values, :]
 
        trace = [go.Bar(x=freq.index, y=freq.iloc[:,0], name=self.my_name),
                 go.Bar(x=freq.index, y=freq.iloc[:,1], name=self.other_name)]
        layout = layout_for_plots
        layout['title'] = 'Most used emojis'
        fig = go.Figure(trace, layout)
        if nb_mode:
            return fig
        plot(fig)
        

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


