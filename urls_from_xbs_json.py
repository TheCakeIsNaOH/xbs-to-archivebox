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
