# Comics Mailer

A python script that notifies you via email whenever your favourite comics are released.

## Installation

Clone this repository using `git`.

### Dependencies

Comics Mailer uses python3. You can install the dependcies using:

```
pip3 install --upgrade feedparser beauutifulsoup4 requests
```

**TODO**: A future version may allow installation through pip.

## Configuration

Before you can use Comics Mailer, you need to configure it. This is done thorugh two main files:

* `$HOME/.config/comics-mailer/params.cfg` is an ini-like configuration file that contains the Mailgun API key and domain used to send emails. See  `params.cfg.template` in this repo for the paramters you need to configure.
* `$HOME/.config/comics-mailer/watchlist.lst` is the list of comics for which you want to receive alerts. Enter a (partial) title on each line; blank lines and lines starting with `#` are ignored, and the matching is case-insensitive.

**TODO**: A future version may include an interactive initial setup procedure.

## Usage

The suggested way to run Comics Mailer is to use schedule a weekly cron job for it. See `man crontab` if you haven't used cron before.

To run the script every Wednesday at 6 pm, you would use the following job:

```
# m h  dom mon dow   command
  0 18 *   *    3    /path/to/comics_mailer.py
```

**Important**: Make sure you have set up your installation as described in [the Configuration section](#configuration). The script will _not_ work unless all the settings are in place.

**TODO**: A future version may be run in a Docker container.

## Credits

Comics Mailer uses data from the awesome comics release lists at [ComicList](http://www.comiclist.com/index.php) and sends emails through the dead-simple [Mailgun](https://www.mailgun.com/) service. This script is made possible by the [BeatifulSoup](https://www.crummy.com/software/BeautifulSoup/) and the [feedparser](https://pypi.python.org/pypi/feedparser) libraries.

