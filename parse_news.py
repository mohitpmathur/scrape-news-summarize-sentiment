# Parse leading indian newsDict sites, and check sentiment

import os
from datetime import datetime
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
from textblob import TextBlob
from nltk.corpus import stopwords
stopword = stopwords.words('english')

def sentiment(text):
    '''
    Retruns sentiment of the text in the range -1 to 1
    text(string): Find sentiment of text

    returns: fraction (sentiment) in range -1 to 1
    '''
    #remove stopwords
    text = [t for t in text.split(" ") if t not in stopword]
    text = " ".join(w for w in text)
    return TextBlob(text).sentiment.polarity

def getHinduArticleText(url):
    '''
    Retrieves the content of the url

    @url: URL for which to retrieve TextBlob

    returns: page content
    '''
    content = ""
    site = urllib2.urlopen(url).read()
    #h = site.decode('utf-8', 'ignore')
    soup = BeautifulSoup(site)
    #print soup.original_encoding
    myDivs = soup.findAll("div", {"class" : "article-text"})
    if len(myDivs) == 0:
        myDivs = soup.findAll("div", {"itemprop" : "articleBody"})
    if len(myDivs) > 0:
        contentPara = myDivs[0].findAll('p', {"class" : "body"})
        for para in contentPara:
            #print para.get_text().strip()
            content += para.get_text().strip()
    return content

def parse_hindu(newsKeys = []):
    site = urllib2.urlopen("http://www.thehindu.com/").read()
    soup = BeautifulSoup(site)
    mydivs = soup.findAll("div", {"class" : "main-content mTop10"})
    contentdivs = mydivs[0].findAll('div', {"data-vr-contentbox" : ""})

    count = 0    
    newsDict = {}
    for tag in contentdivs:
        #htags = tag.findAll(['h1', 'h3'])
        #for htag in htags:
        atags = tag.findAll('a', href=True)
        for atag in atags:
            news_info = []
            news_info.append(pd.to_datetime(datetime.strftime(datetime.now(), "%Y-%m-%d %H")))
            news_info.append('The Hindu')
            if atag.has_attr('data-vr-excerpttitle') and atag.get_text().strip() != "": #atag.string is not None:
                #print atag.get_text().strip(), atag['href']
                if atag.get_text().strip() not in newsDict and \
                atag.get_text().strip() not in newsKeys:
                    news_info.append(atag['href'])
                    newsDict[atag.get_text().strip()] = news_info
                    #newsKeys.append(atag.get_text().strip())
                    count += 1
            else:
                h3tag = atag.find('h3')
                if h3tag is not None:
                    #print h3tag.get_text().strip(), atag['href']
                    if h3tag.get_text().strip() not in newsDict and \
                    atag.get_text().strip() not in newsKeys:
                        news_info.append(atag['href'])
                        newsDict[h3tag.get_text().strip()] = news_info
                        #newsKeys.append(atag.get_text().strip())
                        count += 1
    print "Number of unique newsDict items:",count
    return newsDict

newsDict = {}
newsKeys = []
newsDataFile = 'news_parser.pkl'
if os.path.exists(newsDataFile):
    df = pd.read_pickle(newsDataFile)
    #newsDict = dict(zip(df.Headline, df.URL))
    print "Size of DataFrame before reading news:", df.shape
    newsKeys = df.Headline.tolist()
# Parse The Hindu
newsDict = parse_hindu(newsKeys)

if len(newsDict) > 0:
    temp_df = pd.DataFrame(newsDict.items(), columns=['Headline','All'])
    temp_df = pd.concat([temp_df, temp_df['All'].apply(pd.Series)], axis=1)
    temp_df.columns = ['Headline','All', 'Date_Time','Source','URL']
    temp_df.drop('All', axis=1, inplace=True)
    temp_df['URL_Content'] = temp_df['URL'].map(getHinduArticleText)
    df = pd.concat([df,temp_df], ignore_index=True)
    df.to_pickle(newsDataFile)