#!/usr/bin/python3

import sys, argparse

parser = argparse.ArgumentParser(description='Get bookmarks from an XBrowserSync api')

parser.add_argument('-u', '--url', 
        default='https://api.xbrowsersync.org',
        help='url of the xbrowsersync api service, defaults to https://api.xbrowsersync.org',
        )

required = parser.add_argument_group('required arguments')
required.add_argument('-s', '--sync-id', 
        required=True,
        help='sync ID to get bookmarks from',
        )
required.add_argument('-p', '--password', 
        required=True, 
        help='decryption password',
        )        

args = parser.parse_args()

url = args.url
password = args.password
syncid = args.sync_id

print("url: " + url)
print("password: " + password) 
print("sync ID: " + syncid)