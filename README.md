# whatsappalytics

~ Under development ~

## Summary
This is a toolkit to analyse whatsapp chats. Note that this is still under development so more functionality will be added and it could still be prone to errors. The base files which are used by this toolkit are exported whatsapp chats in .txt format without sent media. Any contributions in form of ideas or code are welcome. 

## Example Usage
In the make_report notebook you will find detailed and commented examples. Click on the upper right corner of the notebook when it is loaded to see it rendered in the nbviewer such that you can see every plot. 

#### Initialize object:
```python
path = "/path/to/your/whatsappbackupt.txt"
languages = ['german', 'english'] # needed to exclude stopwords in wordcloud
exclude = ['Media omitted', 'Audio omitted'] # whatever messages you want to exclude

wa = Whatsapp_Analytics(path, languages=languages, exclude=exclude)
print(wa.names) # show all participants
print(wa.df.tail()) # show last messages for sanity check
```
#### Show some results:
```python
wa.plot_chronology() # plot number of messages sent over time 
wa.plot_overall_participition() # plot percentage of chat participition
wa.plot_wordcloud(who='personx') # plot wordcloud of all messages sent by personx
wa.plot_most_used_emojis(nb_mode=True) # use argument nb_mode=True when you are in a notebook
```
#### Interactive Dash App
You can also make use of the interactive Dash App to see the results. Just run app.py and insert the appearing adress in the browser. Within the app you insert the path to the chat, click on upload and than you can select the plot you would like to see. See example screenshots below (names in legend are blacked):
![Alt text](/screenshots/dash1.png?raw=true "Optional Title")
![Alt text](/screenshots/dash2.png?raw=true "Optional Title")

## Known Issues
- I don't know which kind of formats of exported whatsapp chats exist, so for now this only works for the only two formats (android and iphone) which I have found so far. But other formats could be easily added as soon as I see them. 
- The messages sent by whatsapp itself, for example when someone leaves a group or the "media omitted" strings, can be excluded by the "exclude" argument when initializing the analyser object (see make_report for details). Since I only have the german version I don't know how those strings look like in other languages. 

## Further Ideas 
- Add user defined stopwords to wordcloud
- Add different plot styles (night/day/sunset mode)
- Emoji cloud instead of bar plot (not sure if there exists something) 
- Topic mining improvement (is already implemented but the results are not very good)
- sentiment analysis 
- wordcloud for "hot days" (show the wordcloud only for the most x busiest days)
- ...

