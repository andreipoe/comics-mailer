# Comics Mailer

A python script that notifies you via email whenever your favourite comics are released.

## Installation

Clone this repository using `git`.

### Dependencies

Comics Mailer uses python3. You can install the dependcies using:

```
pip3 install --upgrade feedparser beauutifulsoup4
```

**TODO**: A future version may allow installation through pip.

## Usage

The suggested way to run Comics Mailer is to use schedule a weekly cron job for it. See `man crontab` if you haven't used cron before.

To run the script every Wednesday at 6 pm, you would use the following job:

```
# m h  dom mon dow   command
  0 18 *   *    3    /path/to/comics_mailer.py
```

**TODO**: Before you can send emails, you need to configure your Mailgun parameters.

## Credits

Comics Mailer uses data from the awesome comics release lists at [ComicList](http://www.comiclist.com/index.php) and sends emails through the dead-simple [Mailgun](https://www.mailgun.com/) service. This script is made possible by the [BeatifulSoup](https://www.crummy.com/software/BeautifulSoup/) and the [feedparser](https://pypi.python.org/pypi/feedparser) libraries.

