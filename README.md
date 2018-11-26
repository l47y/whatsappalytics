# whatsappalytics


~ under development ~


## Summary
This is a toolkit to analyse whatsapp chats. Note that this is still under development so more functionality will be added and it could still be prone to errors. The base files which are used by this toolkit are exported whatsapp chats in .txt format without sent media. Any contributions in form of ideas or code are highly appreciated. 


## Usage
In the make_report notebook you will find a notebook with code and detailed comments. Click on the upper right corner of the notebook when it is loaded to see it rendered in the nbviewer such that you can see every plot. Note that the plots are optimized for my own jupyter-notebook style and they don't look that pretty in the default style. 


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



