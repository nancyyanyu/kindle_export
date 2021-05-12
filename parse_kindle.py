import pandas as pd
import numpy as np
import string,argparse,sys

titles = []
texts = []

def main(file):
    with open(file,'r') as f:
        for highlight in f.read().split("=========="):
            lines = highlight.split("\n")[1:]
            if len(lines) < 3 or lines[3] == "":
                continue
            title = lines[0]
            if title[0] == "\ufeff":
                title = title[1:]
            clipping_text = lines[3]
            titles.append(title)
            texts.append(clipping_text)

    df = pd.DataFrame(np.array([titles,texts]).transpose(),columns=['title','note'])
    df['note'] = df['note'].str.strip(string.punctuation)
    return df

if __name__=='__main__':
    # read in command like arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-source", type=str, default="/Volumes/Kindle/documents/My Clippings.txt")
    parser.add_argument("-showtitle", type=bool, default=False)
    parser.add_argument("-title", type=str, default='')
    parser.add_argument("-dest", type=str, default='')
    args = parser.parse_args()
    
    df = main(args.source)
    if args.showtitle==True:
        print('\n\n'.join(df.title.unique().tolist()))
    if args.title!='' and args.dest!='':
        if args.title not in df.title.tolist():
            print("Error: book title is not in file")
            sys.exit()

        else:
            text_file =  open(args.dest,'w') 
            text_file.write('\n\n\n'.join(df[df['title']=='No Filter (Sarah Frier)']['note'].tolist()))
            text_file.close()
                