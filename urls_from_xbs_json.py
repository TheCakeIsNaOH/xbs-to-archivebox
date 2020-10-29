#!/usr/bin/python3

import json
import argparse
import re

#Setup args
parser = argparse.ArgumentParser(
    description='Get filtered list of urls from XBS bookmark json')

required = parser.add_argument_group('required arguments')
required.add_argument('-i','--input',
                      required=True,
                      help='path to file to get json from',
                      )

#Get args
args = parser.parse_args()

#Read in bookmark data
with open(args.input, "r") as inputFile:
    all_bookmarks_raw = inputFile.read()

all_bookmarks = json.loads(all_bookmarks_raw)

#todo:
#   - input blacklist names via args

blacklist_names = ['\[xbs\] Other', 'TestA', 'writing']
blacklist_regex = '(?:% s)' % '|'.join(blacklist_names) 
#print(blacklist_regex)

def filter_bookmarks(bookmarks, blacklist_regex):
    urls = []
    if isinstance(bookmarks, dict):
        if "children" in bookmarks.keys():
            match = re.fullmatch(blacklist_regex, bookmarks['title'])
            if not match:
                urls.extend(filter_bookmarks(bookmarks['children'], blacklist_regex))
            else:
                print('skipping folder ' + bookmarks['title'])
            if "url" in bookmarks.keys():
                print('found url in children dict')
                raise
        elif "url" in bookmarks.keys():
            urls.append(bookmarks['url'])
        else:
            print('did not find children or url in dict')
            raise
    elif isinstance(bookmarks, list):
        for item in bookmarks:
            urls.extend(filter_bookmarks(item, blacklist_regex))
    else:
        print("not sure how you got here, type: ")
        print(type(bookmarks))
    return urls

urls = filter_bookmarks(all_bookmarks, blacklist_regex)
#urls = [item for sublist in nested_urls for item in sublist]

#print(*urls, sep = "\n") 


