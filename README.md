# Comics Mailer

A python script that notifies you via email whenever your favourite comics are released.

## Installation

Clone this repository using `git`.

### Dependencies

Comics Mailer uses python3 and you can install it using `pip3`:

```
pip3 install comics-mailer
```

Alternatively, you can clone this repository and install the dependcies manually using:

```
git clone https://github.com/andreipoe/comics-mailer.git
pip3 install --upgrade feedparser beautifulsoup4 requests
```

## Configuration

Before you can use Comics Mailer, you need to configure it. This is done thorugh two main files:

* `$HOME/.config/comics-mailer/params.cfg` is an ini-like configuration file that contains the Mailgun API key and domain used to send emails. See  `params.cfg.template` in this repo for the paramters you need to configure, or run with `--setup` for an interactive process.
* `$HOME/.config/comics-mailer/watchlist.lst` is the list of comics for which you want to receive alerts. Enter a (partial) title on each line; blank lines and lines starting with `#` are ignored, and the matching is case-insensitive.

## Usage

The suggested way to run Comics Mailer is to use schedule a weekly cron job for it. See `man crontab` if you haven't used cron before.

To run the script every Wednesday at 6 pm, you would use the following job:

```
# m h  dom mon dow   command
  0 18 *   *    3    /path/to/comics_mailer.py
```

**Important**: Make sure you have set up your installation as described in [the Configuration section](#configuration). The script will _not_ work unless all the settings are in place.

### Running in Docker

You can run Comics Mailer in a Docker container. To do this, first obtain the image from DockerHub:

```
docker pull andreipoe/comics-mailer
```

... or build it yourself:

```
docker build -t andreipoe/comics-mailer .
```

Then, set up two directories to hold the application data, for example:

```
mkdir -p /docker-data/comics-mailer/{data,config}
```

Next, set up your configuration as described above and place the relevant files in the `config` folder you have just created. As an alternative, you can run a one-off container to guide you through the setup process.

```
docker run -it --rm -v /docker-data/comics-mailer/data:/comics-mailer/data -v /docker-data/comics-mailer/config:/comics-mailer/config andreipoe/comics-mailer --setup
```

Finally, run the container using your data folders (if you've used the setup container, make sure you use the same data folders in both):

```
docker run -d --name comics-mailer --restart unless-stopped -v /docker-data/comics-mailer/data:/comics-mailer/data -v /docker-data/comics-mailer/config:/comics-mailer/config andreipoe/comics-mailer
```

By default, the application inside the container runs at 6 PM every Wednesday. To override the schedule, set the `CRON` envrionment variable in the container to a valid `cron` string. For example, to run every day at 10 PM you would set `-e CRON='0 22 * * *'` in your `docker run` command (don't forget the quotes, otherwise your shell might try to expand the wildcards).

You will be able to see the application's progress through the `last_run.log` file in the `data` volume.

## Credits

Comics Mailer uses data from the awesome comics release lists at [ComicList](http://www.comiclist.com/index.php) and sends emails through the dead-simple [Mailgun](https://www.mailgun.com/) service. This script is made possible by the [BeatifulSoup](https://www.crummy.com/software/BeautifulSoup/) and the [feedparser](https://pypi.python.org/pypi/feedparser) libraries.

