#!/usr/bin/python3

import sys
import argparse
import urllib.request
import json
import base64
import hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from lzutf8 import Decompressor

# Setup arguments
parser = argparse.ArgumentParser(
    description='Get bookmarks from an XBrowserSync api')

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
required.add_argument('-o', '--output',
                      required=True,
                      help='output file with json',
                      )

#Get args
args = parser.parse_args()
base_url = args.url.strip().rstrip('/')
password = args.password
sync_id = args.sync_id

#Check sync service url
try:
    if urllib.request.urlopen(base_url).getcode() != 200:
        raise BadURL("URL cannot be reached or is not working correctly")
except:
    print("ERROR: URL cannot be reached or is not working correctly. URl: " + base_url)
    sys.exit()

sync_id_url = base_url + "/bookmarks/" + sync_id

#check and download data from sync service
try:
    sync_id_url_response = urllib.request.urlopen(sync_id_url)
    if sync_id_url_response.getcode() != 200:
        raise BadURL("URL cannot be reached or is not working correctly")
    sync_data_encrypted_raw = sync_id_url_response.read().decode('utf-8')
    sync_id_url_response.close()
except:
    print("ERROR: URL cannot be reached or is not working correctly.")
    print("Check that your sync ID is correct.")
    print("URl: " + base_url)
    sys.exit()

#Get encrypted bookmark data from json response from api query
sync_data_encrypted = json.loads(sync_data_encrypted_raw)
all_bookmarks_encrypted = base64.b64decode(sync_data_encrypted["bookmarks"])

#Setup decryption key and parameters
key = hashlib.pbkdf2_hmac('sha256', password.encode(
    'utf-8'), sync_id.encode('utf-8'), 250000, 32)
nonce_iv = all_bookmarks_encrypted[:16]
ciphertext = all_bookmarks_encrypted[16:-16]
tag = all_bookmarks_encrypted[-16:]

#Decrypt bookmark data
cipher = AES.new(key, AES.MODE_GCM, nonce=nonce_iv)
all_bookmarks_decrypted = cipher.decrypt_and_verify(ciphertext, tag)

#Decompress bookmark data with lzutf8
decompressor = Decompressor()
all_bookmarks_decompressed = decompressor.decompressBlockToString(
    all_bookmarks_decrypted)

#Prettify decrypted bookmark data
all_bookmarks_json = json.loads(all_bookmarks_decompressed)
all_bookmarks_decompressed = json.dumps(all_bookmarks_json, indent=4)

#Write bookmark data to file
with open(args.output, "w") as outputFile:
    outputFile.write(all_bookmarks_decompressed)
