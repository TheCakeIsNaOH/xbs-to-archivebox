#!/usr/bin/python3

import json
import argparse

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
#   - filter via regex rather then "in"
#   - how to return list rather then print
#   - input blacklist names via args

blacklist_names = ['[xbs] Other', 'TestA']

def get_filter(bookmarks, blacklist_names):
    
    if isinstance(bookmarks, dict):
        if "children" in bookmarks.keys():
            if bookmarks['title'] not in blacklist_names:
                get_filter(bookmarks['children'], blacklist_names)
            if "url" in bookmarks.keys():
                print('found url in children dict')
                raise
        elif "url" in bookmarks.keys():
            print(bookmarks['url'])
        else:
            print('did not find children or url in dict')
            raise
    elif isinstance(bookmarks, list):
        for item in bookmarks:
            get_filter(item, blacklist_names)
    else:
        print("not sure how you got here, type: ")
        print(type(bookmarks))

get_filter(all_bookmarks, blacklist_names)




