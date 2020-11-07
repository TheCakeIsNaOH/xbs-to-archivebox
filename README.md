Download your bookmarks from [xBrowserSync](https://www.xbrowsersync.org/), filter them, and save them into [ArchiveBox](https://archivebox.io/)

Requires python3 with the `pycryptodomex` package installed.

First, run `get_xbs_bookmarks.py` to get a file with the json formatted raw bookmark data from xBrowserSync.
Then, run `urls_from_xbs_json.py` to filter the raw json bookmark data into a list of URLs.
Finally, run `archivebox add < /path/to/urls.txt` to import the url list into archivebox.

See the options by running the python scripts with `-h`.

The optional filtering in `urls_from_xbs_json.py` is a straight search, wildcards/regex not supported at the moment. 