#!/usr/bin/env python3

import re
import sys
import os.path
import requests
from pathlib import Path
from configparser import ConfigParser

import feedparser
from bs4 import BeautifulSoup as soup

# Config files
CONFIG_FOLDER         = Path.home() / '.config/comics-mailer'
CONFIG_FILE_PARAMS    = str(CONFIG_FOLDER / 'params.cfg')
CONFIG_FILE_WATCHLIST = str(CONFIG_FOLDER / 'watchlist.lst')

# Config keys
CONFIG_SECTION_MAILGUN    = 'mailgun'
CONFIG_KEY_MAILGUN_KEY    = 'api_key'# Your API key
CONFIG_KEY_MAILGUN_DOMAIN = 'domain' # Your doimain name in your base API URL
CONFIG_KEY_MAILGUN_FROM   = 'from'   # The email sender, e.g. as "Name <email@tld.me>"
CONFIG_KEY_MAILGUN_TO     = 'to'     # The recipient, e.g. as "Name <email@tld.me>"

# Email preferences
MAILGUN_SUBJECT_UPDATE = '[comics-mailer] New watched comics available!'
MAILGUN_BODY_UPDATE    = '''\
My Lord,

$n new comics from your watchlist have been shipped:

$c

God speed,

Comics Mailer'''
MAILGUN_SUBJECT_ERROR = '[comics-mailer] Could not complete your comics update check'
MAILGUN_BODY_ERROR    = '''\
My master,

I have failed you. The following error occured when checking for updates to your watched comics: $e.

$m

With great regret,

Comics Mailer'''

# ComicsList
FEED_URL = 'http://feeds.feedburner.com/ncrl'

# TODO: remove debugging
DEBUG = True

# Error codes
ERR_NO_FEED        = -1
ERR_INVALID_PARAMS = -2
ERR_NO_CONFIG      = -3
ERR_NO_WATCHLIST   = -4

# Error code messages
ERR_MSG_NO_FEED = 'Could not retrieve the comics feed from ComicList.com. Double check your URL and make sure that the site is still up.'
ERR_MSG_GENERIC = "You'd have to check the code to figure out what this error means (they're all labeled towards the top)."

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

    for k in [CONFIG_KEY_MAILGUN_KEY, CONFIG_KEY_MAILGUN_DOMAIN, CONFIG_KEY_MAILGUN_FROM, CONFIG_KEY_MAILGUN_TO]:
        if k not in config[CONFIG_SECTION_MAILGUN]:
            err_exit("Invailid Mailgun configuration. Please check the config file at " + \
                CONFIG_FILE_PARAMS + " and see the README for details.", ERR_INVALID_PARAMS)

    return config[CONFIG_SECTION_MAILGUN][CONFIG_KEY_MAILGUN_KEY], \
        config[CONFIG_SECTION_MAILGUN][CONFIG_KEY_MAILGUN_DOMAIN], \
        config[CONFIG_SECTION_MAILGUN][CONFIG_KEY_MAILGUN_FROM],   \
        config[CONFIG_SECTION_MAILGUN][CONFIG_KEY_MAILGUN_TO]

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

# Send an email using the mailgun API
def send_mailgun(subject, body):
    api_url = "https://api.mailgun.net/v3/" + mailgun_domain + "/messages"

    return requests.post(api_url, auth=("api", mailgun_key), data={
            "from": mailgun_from,
            "to": [mailgun_to],
            "subject": subject,
            "text": body})

# Send an error email when the check cannot be performed
# TODO: Add a parameter to disable error emails
def send_mail_error(errcode):
    body = MAILGUN_BODY_ERROR.replace('$e', str(errcode))

    if errcode == ERR_NO_FEED:
        err_msg = ERR_MSG_NO_FEED
    else:
        err_msg = ERR_MSG_GENERIC
    body = body.replace('$m', err_msg)

    resp = send_mailgun(MAILGUN_SUBJECT_ERROR, body)

    if DEBUG:
        print("Sent error mail to", mailgun_to, 'for code', errcode, 'explaining that:', err_msg)
        print("Reponse was:", resp)

# Send an update email when matched comics are found
def send_mail_update(comics):
    comics_list = ('\n'.join(['  * ' + c for c in comics]))
    body        = MAILGUN_BODY_UPDATE.replace('$n', str(len(comics))).replace('$c', comics_list)

    resp = send_mailgun(MAILGUN_SUBJECT_UPDATE, body)

    if DEBUG:
        print("Sent update mail to", mailgun_to, 'for', len(comics), 'comics:\n' + comics_list)
        print("Reponse was:", resp)


# Get the title and hash from an RSS feed entry
def get_entry_details(entry):
    r = re.compile('Hash: ([\w\d]{40})')
    hash = r.search(entry.summary).group(1)

    return entry.title, hash

# Get the RSS feed
def get_rss_entries():
    feed = feedparser.parse(FEED_URL)
    if len(feed.entries) == 0 or 'bozo_exception' in feed:
        send_mail_error(ERR_NO_FEED)
        err_exit("Could not retrieve feed contents. Is your URL working?", ERR_NO_FEED)

    return feed.entries

# Get the CSV comic list in an RSS entry
def parse_comic_list(entry):
    return list(soup(entry.summary, "lxml").find_all('p')[4].stripped_strings)

# Return a list of the comics matched from the watchlist
def match_comics(comics, watchlist, only_once=True):
    # Filter based on watchlist
    matched = [c for watched in watchlist for c in comics if watched.lower() in c.lower()]

    # Remove non-comics from list, e.g. games and merch
    matched = [c.split(',')[2] for c in matched if c.split(',')[1].upper() == c.split(',')[1]]

    # There may be several variants of the same comic being released at the same time, so it is often
    # redundant to consider all titles that match
    if only_once:
        # Keep the title only
        title_only = re.compile(r'[^#]+#[\d]+')
        matched = [title_only.match(c).group() for c in matched if title_only.match(c)]

        # Remove duplicates
        matched = list(set(matched))

    return matched

if __name__ == '__main__':
    # TODO: Consider adding CLI arguments for the mailgun params
    # TODO: add a --setup option that walks thourgh typing in the settings and setting the watch list

    mailgun_key, mailgun_domain, mailgun_from, mailgun_to = read_mailgun_params()
    paramlist = [mailgun_key, mailgun_domain, mailgun_from, mailgun_to]
    if None in paramlist:
        err_exit("Invailid Mailgun configuration. Please check the config file at " + \
                CONFIG_FILE_PARAMS + " and see the README for details.", ERR_INVALID_PARAMS)

    if DEBUG:
        print("Params:", paramlist)
        # sys.exit(0)

    watchlist = read_watchlist()
    if not watchlist:
        err_exit("You have no watched comics. Please place your comics in " + \
            CONFIG_FILE_WATCHLIST + ". See the README for details.", ERR_NO_WATCHLIST)

    # Use only the latest week
    # TODO: Use all entries since the last update
    latest = get_rss_entries()[0]

    # TODO: parameter to show only one match per watch comic
    comics  = parse_comic_list(latest)
    matched = match_comics(comics, watchlist)
    send_mail_update(matched)
    # TODO: save the date of the last update

