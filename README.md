# whatsappalytics


## Summary
This is a toolkit to analyse whatsapp chats. Used in a notebook it can produce a nice report of one of your chats.
Not that this is still under development so more functionality will be added and it could still be prone to errors.
The base files which are used by this toolkit are exported whatsapp chats in .txt format without sent media

## Issues
- I don't know which kind of formats of exported whatsapp chats exist, so for now this only works for the following format:   
15.04.18, 20:43 - Name1: text of message...        
19.04.18, 21:51 - Name2: text of message...       
But other formats could be easily added as soon as I see them. 
- I still have to figure out which is the exact string used in the .txt file when media is excluded.
  
## Example 
See make_report for an example. Click on the upper right corner of the notebook to see it rendered in the nbviewer such that you can see every plot. 

## Further Ideas / TODOs
- Add user defined stopwords to wordcloud
- Add a different plot style (the current one looks more beautiful in my local jupyter-notebook where the background is dark grey)
- Test IOS format of exported chat
- Emoji cloud instead of bar plot (not sure if something exists...) 

