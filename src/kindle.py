import os
import re
import sys
import time
import urllib
import string
import argparse
import platform
import requests
import sqlite3
import subprocess
import pandas as pd
import numpy as np
from googletrans import Translator
from os.path import expanduser
from lxml import html

HOME= expanduser("~")

vocab_dir = "/Volumes/Kindle/system/vocabulary/vocab.db"
clip_dir = "/Volumes/Kindle/documents/My Clippings.txt"
con = sqlite3.connect(vocab_dir)
cur = con.cursor()

def fetch_bookname():
    cur.execute('''select title from BOOK_INFO;''')
    bn = cur.fetchall()
    return bn

def fetch_words(book):
    q_word = """select ta.word,ta.stem, tb.usage from ((select  id, word, stem from WORDS) ta inner join (select word_key,usage from LOOKUPS where book_key=(select id from BOOK_INFO where title="{book_name}") ) tb on ta.id==tb.word_key) ;""".format(book_name=book)
    cur.execute(q_word)
    data = cur.fetchall()
    words = pd.DataFrame(data,columns = ['word','stem','usage'])
    return words

def eng_to_cn(word,src = 'youdao'):
    if src =='youdao':
        url = "https://www.youdao.com/w/{}/#keyfrom=dict2.top".format(urllib.parse.quote(word))
        page = requests.get(url)
        tree = html.fromstring(page.content)
        xpath = '//*[@id="phrsListTab"]//div[@class="trans-container"]/ul/li/text()'
        output = tree.xpath(xpath)
        if output!=[]:
            return ',\n'.join(output)
        else:
            xpath = '//div[@id="tWebTrans"]/div[not(@id)]//div[@class="title"]//span/text()'
            output = tree.xpath(xpath)
        if output!=[]:
            return ',\n'.join(output)
        else:
            return ''
        
    elif src =='google':
        translator = Translator()
        output = translator.translate(word, dest='zh-cn').text
        return output


def fetch_note(book):
    text = []
    with open(clip_dir,'r') as f:
        for highlight in f.read().split("=========="):
            lines = highlight.split("\n")[1:]
            if len(lines) < 3 or lines[3] == "":
                continue
            title = lines[0]
            if title[0] == "\ufeff":
                title = title[1:]
            if title.startswith(book):
                text.append(lines[3])
    note = pd.DataFrame(np.array([text]).transpose(),columns=['note'])
    note['title']=book
    return note

def main():
    bn = fetch_bookname()
    bn_op = ["{}. {}".format(i,b[0]) for i, b in enumerate(bn)]
    print("Books:")
    print("=========")
    print('\n'.join(bn_op))
    print("=========")

    print()
    book = bn[int(input("Which book do you want to query? (Insert book index) "))][0]
    print(book)
    note = fetch_note(book).head(1)
    words = fetch_words(book).head(1)
    print()
    print("=========")

    print()
    if_trans = input("Words list is fetched. Do you want to translate all the words? [y/n]")
    if if_trans=='y':
        words['trans'] = words['stem'].apply(eng_to_cn)
        print("Translation is completed.")
    word_dir = os.path.join(HOME,book+' Word.csv')
    words.to_csv(word_dir,index=False)
    print("Words directory: "+word_dir)
    print()
    print("=========")

    print()
    if_trans_note = input("Notes are fetched. Do you want to translate them all? [y/n]")
    if if_trans_note=='y':
        note['len_'] = note['note'].str.strip(string.punctuation).str.split().apply(len)
        note.loc[note['len_']==1,'trans'] = note.loc[note['len_']==1,'note'].apply(lambda x: eng_to_cn(x,'youdao'))
        note.loc[note['len_']>1,'trans']  = note.loc[note['len_']>1,'note'].apply(lambda x: eng_to_cn(x,'google'))
        del note['len_']
        print("Translation is completed.")
    note_dir = os.path.join(HOME,book+' Note.csv')
    note.to_csv(note_dir,index=False)
    print("Notes directory: "+note_dir)
    print()
    print("=========")
    
    
    
if __name__=="__main__":
    main()