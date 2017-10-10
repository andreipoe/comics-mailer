#!/usr/bin/env python3

import re
import sys
import os
import os.path
import requests
import itertools
from pathlib import Path
from configparser import ConfigParser
from datetime import date
from argparse import ArgumentParser

import feedparser
from bs4 import BeautifulSoup as soup

# Config files
CONFIG_FOLDER         = Path.home() / '.config/comics-mailer'
CONFIG_FILE_PARAMS    = str(CONFIG_FOLDER / 'params.cfg')
CONFIG_FILE_WATCHLIST = str(CONFIG_FOLDER / 'watchlist.lst')
CONFIG_FOLDER         = str(CONFIG_FOLDER) # os.path methods require a string

# Config keys
CONFIG_SECTION_MAILGUN    = 'mailgun'
CONFIG_KEY_MAILGUN_KEY    = 'api_key' # Your API key
CONFIG_KEY_MAILGUN_DOMAIN = 'domain'  # Your doimain name in your base API URL
CONFIG_KEY_MAILGUN_FROM   = 'from'    # The email sender, e.g. as "Name <email@tld.me>"
CONFIG_KEY_MAILGUN_TO     = 'to'      # The recipient, e.g. as "Name <email@tld.me>"

CONFIG_SECTION_BEHAVIOUR               = 'behaviour'
CONFIG_KEY_BEHAVIOUR_MAIL_ON_ERROR     = 'mail_on_error' # Whether to send an email when an error occurs, detailing the error
CONFIG_DEFAULT_BEHAVIOUR_MAIL_ON_ERROR = True

# Data files
DATA_FOLDER           = Path.home() / '.local/share/comics-mailer'
DATA_FILE_LAST_UPDATE = str(DATA_FOLDER / 'last_update')
DATA_FOLDER           = str(DATA_FOLDER) # os.path methods require a string

# Email text
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

# TODO: disable debugging
DEBUG_NOMAIL      = 'nomail'
DEBUG_PARAMS      = 'params'
DEBUG_DATA        = 'data'
DEBUG_WATCHLIST   = 'watchlist'
DEBUG_FORCEUPDATE = 'forceupdate'
# DEBUG           = "|".join([DEBUG_PARAMS, DEBUG_NOMAIL, DEBUG_DATA, DEBUG_FORCEUPDATE])
DEBUG             = ''

# Error codes
ERR_NO_FEED        = -1
ERR_INVALID_PARAMS = -2
ERR_NO_CONFIG      = -3
ERR_NO_WATCHLIST   = -4

# Error code messages
ERR_MSG_NO_FEED   = 'Could not retrieve the comics feed from ComicList.com. Double check your URL and make sure that the site is still up.'
ERR_MSG_NO_CONFIG = "No configuration file found at at " + CONFIG_FILE_PARAMS + ". Please see the README for details on creating one."
ERR_MSG_GENERIC   = "You'd have to check the code to figure out what this error means (they're all labeled towards the top)."

# Global behaviour settings
behaviour_mail_on_error = CONFIG_DEFAULT_BEHAVIOUR_MAIL_ON_ERROR

# Print an error message and exit
def err_exit(msg, code=1):
    print(msg, file=sys.stderr)

    if behaviour_mail_on_error:
        send_mail_error(code, msg)

    sys.exit(code)

# Read the required mailgun parameters from the config file
def read_mailgun_params():
    if not os.path.isfile(CONFIG_FILE_PARAMS):
        err_exit(ERR_MSG_NO_CONFIG, ERR_NO_CONFIG)

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

# Read custom behaviour parameters from the config file
def read_behaviour_params():
    if not os.path.isfile(CONFIG_FILE_PARAMS):
        err_exit(ERR_MSG_NO_CONFIG, ERR_NO_CONFIG)

    config = ConfigParser()
    config.read(CONFIG_FILE_PARAMS)

    try:
        behaviour_section = config[CONFIG_SECTION_BEHAVIOUR]
        mail_on_error     = behaviour_section.getboolean(CONFIG_KEY_BEHAVIOUR_MAIL_ON_ERROR, CONFIG_DEFAULT_BEHAVIOUR_MAIL_ON_ERROR)

        return mail_on_error
    except KeyError:
        return CONFIG_DEFAULT_BEHAVIOUR_MAIL_ON_ERROR

# Read the watched comics list
def read_watchlist():
    if not os.path.isfile(CONFIG_FILE_WATCHLIST):
        err_exit("You have no watched comics. Please place your comics in " + \
            CONFIG_FILE_WATCHLIST + ". See the README for details.", ERR_NO_WATCHLIST)

    with open(CONFIG_FILE_WATCHLIST, 'r') as f:
        watchlist = [line.strip() for line in f if line.strip() != '' and not line.strip().startswith('#')]

    return watchlist

# Read the date of the last update from the data file
def get_last_update():
    if DEBUG_FORCEUPDATE in DEBUG:
        return None

    try:
        with open(DATA_FILE_LAST_UPDATE, 'r') as f:
            isodate = f.read().strip()
            try:
                parts   = isodate.split('-')
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                return date(y, m, d)
            except ValueError:
                print("Invalid last update:", isodate, file=sys.stderr)
    except FileNotFoundError: # No last update
        return None

# Update the data file with the current date
def save_last_update():
    if DEBUG_FORCEUPDATE in DEBUG:
        return

    if not os.path.isdir(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    try:
        with open(DATA_FILE_LAST_UPDATE, 'w') as f:
            f.write(date.today().isoformat())
    except IOError:
        print("Failed to save update timestamp. The nextrun might include repeating results.\
            Do you have permissions to write to", DATA_FILE_LAST_UPDATE + '?', file=sys.stderr)

# Send an email using the mailgun API
def send_mailgun(subject, body):
    if DEBUG_NOMAIL in DEBUG:
        return 'Emails disabled for debugging.'

    api_url = "https://api.mailgun.net/v3/" + mailgun_domain + "/messages"

    return requests.post(api_url, auth=("api", mailgun_key), data={
            "from": mailgun_from,
            "to": [mailgun_to],
            "subject": subject,
            "text": body})

# Send an error email when the check cannot be performed
def send_mail_error(errcode, msg=None):
    body = MAILGUN_BODY_ERROR.replace('$e', str(errcode))

    if errcode == ERR_NO_FEED:
        err_msg = ERR_MSG_NO_FEED
    elif errocode == ERR_NO_CONFIG:
        err_msg = ERR_MSG_NO_CONFIG
    elif msg is not None:
        err_msg = msg
    else:
        err_msg = ERR_MSG_GENERIC
    body = body.replace('$m', err_msg)

    resp = send_mailgun(MAILGUN_SUBJECT_ERROR, body)

    if DEBUG:
        print("Sent error mail to", mailgun_to, 'for code', errcode, 'explaining that:', err_msg)
        print("Reponse was:", resp)

# Send an update email when matched comics are found
def send_mail_update(comics):
    comics_list = '\n'.join(['  * ' + c for c in sorted(comics)])
    body        = MAILGUN_BODY_UPDATE.replace('$n', str(len(comics))).replace('$c', comics_list)

    resp = send_mailgun(MAILGUN_SUBJECT_UPDATE, body)

    if DEBUG:
        print("Sent update mail to", mailgun_to, 'for', len(comics), 'comics:\n' + comics_list)
        print("Reponse was:", resp)


# Get the date from an entry's title
def get_entry_date(entry):
    r = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})')
    m = r.search(entry.title)
    return date(*[int(i) for i in r.search(entry.title).group(3, 1, 2)])

# Get the RSS feed
def get_rss_entries(since=None):
    feed = feedparser.parse(FEED_URL)
    if len(feed.entries) == 0 or 'bozo_exception' in feed:
        err_exit("Could not retrieve feed contents. Is your URL working?", ERR_NO_FEED)

    if since is None:
        return feed.entries
    else:
        return [e for e in feed.entries if get_entry_date(e) > since]

def parse_comic_list(entries):
    return list(itertools.chain.from_iterable([soup(e.summary, 'html.parser').find_all('p')[4].stripped_strings for e in entries]))

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

def parse_cli_args():
    parser = ArgumentParser(description="Send email notifications if new watched comics are available.")

    parser.add_argument('--clean', '-c', action='store_true', help='Ignore last updates and perform a clean run. May result in receiving notification about comics seen previously.')
    parser.add_argument('--all-versions', '-a', action='store_true', help='Show all versions of a comic, for example variant covers. Without this option, only the main title is shown.')

    return parser.parse_args()

if __name__ == '__main__':
    # TODO: Consider adding CLI arguments for the mailgun params
    # TODO: add a --setup option that walks thourgh typing in the settings and setting the watch list

    cli_args = parse_cli_args()

    # Read the Mailgun config parameters
    mailgun_key, mailgun_domain, mailgun_from, mailgun_to = read_mailgun_params()
    paramlist = [mailgun_key, mailgun_domain, mailgun_from, mailgun_to]
    if None in paramlist:
        err_exit("Invailid Mailgun configuration. Please check the config file at " + \
                CONFIG_FILE_PARAMS + " and see the README for details.", ERR_INVALID_PARAMS)

    if DEBUG_PARAMS in DEBUG:
        print("Params:", paramlist)

    # Read the behaviour config paramters
    behaviour_mail_on_error = read_behaviour_params()

    if DEBUG_PARAMS in DEBUG:
        print("Mail on error:", behaviour_mail_on_error)

    # Read the watchlist
    watchlist = read_watchlist()
    if not watchlist:
        err_exit("You have no watched comics. Please place your comics in " + \
            CONFIG_FILE_WATCHLIST + ". See the README for details.", ERR_NO_WATCHLIST)
    if DEBUG_WATCHLIST in DEBUG:
        print("Watchlist:", watchlist)

    # Read the last update date
    last_update = get_last_update()
    print("Last update:", last_update)

    # Use only the latest week, unless a clean run is requested
    if cli_args.clean:
        last_update = None
        print("Ignoring last update")
    updates = get_rss_entries(last_update)
    if DEBUG:
        print(len(updates), "updates")

    keep_title_only = not cli_args.all_versions
    comics          = parse_comic_list(updates)
    matched         = match_comics(comics, watchlist, keep_title_only)
    if len(matched) > 0:
        send_mail_update(matched)
    else:
        print("No newer comics available.")

    # Save the date of the last update
    save_last_update()

    # TODO: add an option to keep a local log of all matches

