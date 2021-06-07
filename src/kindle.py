import os
import re
import sys,csv
import time
import string
import logging
import argparse
import platform
import requests
import sqlite3
import subprocess
import pandas as pd
import numpy as np
from time import sleep
from googletrans import Translator
from os.path import expanduser
from lxml import html

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("urllib3").setLevel(logging.WARNING)


HOME= expanduser("~")
DATA_DIR = os.path.join(os.getcwd(),'data')
if not os.path.isdir(DATA_DIR): os.mkdir(DATA_DIR)

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

def eng_to_cn(row,word_file,total_len):
    if 'stem' in row.index:
        word = row['stem']
    elif 'note' in row.index:
        word = row['note']
    
    if len(word.split())<3:
        
        url = "https://www.youdao.com/w/{}/#keyfrom=dict2.top".format(word)
        
        try:
            page = requests.get(url)
        except requests.exceptions.ConnectionError:
            logging.debug("Connection refused")
            sleep(5)

        tree = html.fromstring(page.content)
        xpath = '//*[@id="phrsListTab"]//div[@class="trans-container"]/ul/li/text()'
        output = tree.xpath(xpath)
        if output!=[]:
            output = ',\n'.join(output)
        else:
            xpath = '//div[@id="tWebTrans"]/div[not(@id)]//div[@class="title"]//span/text()'
            output = tree.xpath(xpath)
        if output!=[]:
            output = ''.join(output)
        else:
            output = ''
        
    else:
        
        translator = Translator()
        output = translator.translate(word, dest='zh-cn').text
        
    row = row.to_dict()
    row['trans']=output
    write_row(row,word_file)
    
    remain = total_len-row['index']
    if remain%20==0:
        logging.info(str(remain)+' remaining')
    return output
    

def write_row(row,word_file):
    csv_col = row.keys()
    with open(word_file,'a') as file:
        writer = csv.DictWriter(file,fieldnames = list(csv_col))            
        writer.writerow(row)
            
            
def write_header(csv_col,word_file):
    with open(word_file,'w') as file:
        writer = csv.DictWriter(file,fieldnames = list(csv_col))            
        writer.writeheader()
        
        
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
    note = fetch_note(book)
    words = fetch_words(book).reset_index()
    print()
    print("=========")

    print()
    if_trans = input("Words list is fetched. Do you want to translate all the words? [y/n] ")
    word_file = os.path.join(DATA_DIR ,book+' Word.csv')
    if if_trans=='y':
        
        write_header(list(words.columns)+['trans'],word_file)
        words.apply(lambda x:eng_to_cn(x,word_file,len(words)),axis=1)
        print("Translation is completed.")
    words.to_csv(word_file,index=False)
    print("Words directory: "+word_file)
    print()
    print("=========")

    print()
    if_trans_note = input("Notes are fetched. Do you want to translate them all? [y/n] ")
    note_file = os.path.join(DATA_DIR ,book+' Note.csv')
    if if_trans_note=='y':
        
        write_header(list(note.columns)+['trans'],note_file)
        note.apply(lambda x: eng_to_cn(x,note_file,len(note)),axis=1)
        print("Translation is completed.")
    note.to_csv(note_file,index=False)
    print("Notes directory: "+note_file)
    print()
    print("=========")
    
    
if __name__=="__main__":
    main()