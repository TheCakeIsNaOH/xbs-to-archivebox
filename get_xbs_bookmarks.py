#!/usr/bin/python3

import sys
import argparse
import urllib.request
import json

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

base_url = args.url.strip().rstrip('/')
password = args.password
syncid = args.sync_id

try:
    if urllib.request.urlopen(base_url).getcode() != 200:
        raise BadURL("URL cannot be reached or is not working correctly")
except:
    print("ERROR: URL cannot be reached or is not working correctly. URl: " + base_url)
    sys.exit()

sync_id_url = base_url + "/bookmarks/" + syncid

try:
    sync_id_url_response = urllib.request.urlopen(sync_id_url)
    if sync_id_url_response.getcode() != 200:
        raise BadURL("URL cannot be reached or is not working correctly")
    sync_data_encrypted_raw = sync_id_url_response.read().decode('utf-8')
    sync_id_url_response.close()
except:
    print("ERROR: URL cannot be reached or is not working correctly. Check that your sync ID is correct.")
    print("URl: " + base_url)
    sys.exit()

