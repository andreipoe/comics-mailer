#!/usr/bin/env python3

import re
import sys

import feedparser
from bs4 import BeautifulSoup as soup

FEED_URL = 'http://feeds.feedburner.com/ncrl'

# TODO: remove debugging
DEBUG = True

ERR_NO_FEED = -1

# Deprecated
def make_feed_url(base, query):
    return base + query.replace(' ', '+')

# TODO: Mail on error
def send_mail_error(errcode):
    pass

# TODO: Mail on success
def send_mail_update():
    pass

# Get the title and hash from an RSS feed entry
def get_entry_details(entry):
    r = re.compile('Hash: ([\w\d]{40})')
    hash = r.search(entry.summary).group(1)

    return entry.title, hash

# Get the RSS feed
def get_rss_entries():
    feed = feedparser.parse(FEED_URL)
    if len(feed.entries) == 0 or 'bozo_exception' in feed:
        print("Could not retrieve feed contents. Is your URL working?")
        if not DEBUG:
            send_mail_error(ERR_NO_FEED)
        sys.exit(ERR_NO_FEED)

    return feed.entries

# Get the CSV comic list in an RSS entry
def parse_comic_list(entry):
    return list(soup(entry.summary, "lxml").find_all('p')[4].stripped_strings)

if __name__ == '__main__':
    # TODO: Read the Mailgun params from a config file and/or CLI arguments.

    # Use only the latest week
    # TODO: Use all entries since the last update
    latest = get_rss_entries()[0]

    comics = parse_comic_list(latest)
    # TODO: get a list of watched comics and seatch through the csv
    # TODO: send a mailgun for the matched comics
    # TODO: save the date of the last update

