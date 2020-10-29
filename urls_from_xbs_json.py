#!/usr/bin/python3

import json
import argparse
import re

#Setup args
parser = argparse.ArgumentParser(
    description='Get filtered list of urls from XBS bookmark json')

parser.add_argument('-m', '--filter-directories',
                    nargs='+',
                    dest='dirs',
                    help='list of directory names to exclude, space separated, enclose in double quotes, case insensitive'
                    )

required = parser.add_argument_group('required arguments')
required.add_argument('-i','--input',
                      required=True,
                      help='path to file to get json from',
                      )
required.add_argument('-o', '--output',
                      required=True,
                      help='output file with urls',
                      )

#Get args
args = parser.parse_args()

#Read in bookmark data
with open(args.input, "r") as inputFile:
    all_bookmarks_raw = inputFile.read()

all_bookmarks = json.loads(all_bookmarks_raw)

#Get regex match object from args
blacklist_names = []
for directory in args.dirs:
    blacklist_names.append(re.escape(directory.strip("'")))
blacklist_regex_string = '(?:% s)' % '|'.join(blacklist_names)
blacklist_regex = re.compile(blacklist_regex_string, re.IGNORECASE)

#filter bookmark folders, return urls in non-blacklisted folders
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

with open(args.output, "w") as outputFile:
    for url in urls:
        outputFile.write(url + "\n")

