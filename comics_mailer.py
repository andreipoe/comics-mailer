#!/usr/bin/env python3

import re
import sys
import os.path
from pathlib import Path
from configparser import ConfigParser

import feedparser
from bs4 import BeautifulSoup as soup

CONFIG_FOLDER         = os.path.join(Path.home(), '.config/comics-mailer')
CONFIG_FILE_PARAMS    = os.path.join(CONFIG_FOLDER, 'params.cfg')
CONFIG_FILE_WATCHLIST = os.path.join(CONFIG_FOLDER, 'watchlist.lst')

CONFIG_SECTION_MAILGUN    = 'mailgun'
CONFIG_KEY_MAILGUN_KEY    = 'api_key'
CONFIG_KEY_MAILGUN_DOMAIN = 'domain'

FEED_URL = 'http://feeds.feedburner.com/ncrl'

# TODO: remove debugging
DEBUG = True

ERR_NO_FEED        = -1
ERR_INVALID_PARAMS = -2
ERR_NO_CONFIG      = -3
ERR_NO_WATCHLIST   = -4

# Print an error message and exit
def err_exit(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)

# Read the required mailgun parameters from the config file
def read_mailgun_params():
    if not os.path.isfile(CONFIG_FILE_PARAMS):
        err_exit("No configuration file found at at " + CONFIG_FILE_PARAMS + \
            ". Please see the README for details on creating one.", ERR_NO_CONFIG)

    config = ConfigParser()
    config.read(CONFIG_FILE_PARAMS)

    for s in [CONFIG_SECTION_MAILGUN]:
        if s not in config:
            err_exit("Invailid Mailgun configuration. Please check the config file at " + \
                CONFIG_FILE_PARAMS + " and see the README for details.", ERR_INVALID_PARAMS)

    for k in [CONFIG_KEY_MAILGUN_KEY, CONFIG_KEY_MAILGUN_DOMAIN]:
        if k not in config[CONFIG_SECTION_MAILGUN]:
            err_exit("Invailid Mailgun configuration. Please check the config file at " + \
                CONFIG_FILE_PARAMS + " and see the README for details.", ERR_INVALID_PARAMS)

    return config[CONFIG_SECTION_MAILGUN][CONFIG_KEY_MAILGUN_KEY], \
        config[CONFIG_SECTION_MAILGUN][CONFIG_KEY_MAILGUN_DOMAIN]

# Read the watched comics list
def read_watchlist():
    if not os.path.isfile(CONFIG_FILE_WATCHLIST):
        err_exit("You have no watched comics. Please place your comics in " + \
            CONFIG_FILE_WATCHLIST + ". See the README for details.", ERR_NO_WATCHLIST)

    with open(CONFIG_FILE_WATCHLIST, 'r') as f:
        watchlist = [line.strip() for line in f if line.strip() != '' and not line.strip().startswith('#')]

    return watchlist

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
        err_exit("Could not retrieve feed contents. Is your URL working?", ERR_NO_FEED)
        if not DEBUG:
            send_mail_error(ERR_NO_FEED)

    return feed.entries

# Get the CSV comic list in an RSS entry
def parse_comic_list(entry):
    return list(soup(entry.summary, "lxml").find_all('p')[4].stripped_strings)

if __name__ == '__main__':
    # TODO: Consider adding CLI arguments for the mailgun params
    # TODO: add a --setup option that walks thourgh typing in the settings and setting the watch list

    mailgun_key, mailgun_domain = read_mailgun_params()
    if not mailgun_key or not mailgun_domain:
        err_exit("Invailid Mailgun configuration. Please check the config file at " + \
                CONFIG_FILE_PARAMS + " and see the README for details.", ERR_INVALID_PARAMS)

    watchlist = read_watchlist()
    if not watchlist:
        err_exit("You have no watched comics. Please place your comics in " + \
            CONFIG_FILE_WATCHLIST + ". See the README for details.", ERR_NO_WATCHLIST)

    # Use only the latest week
    # TODO: Use all entries since the last update
    latest = get_rss_entries()[0]

    comics = parse_comic_list(latest)
    # TODO: get a list of watched comics and seatch through the csv
    # TODO: send a mailgun for the matched comics
    # TODO: save the date of the last update

