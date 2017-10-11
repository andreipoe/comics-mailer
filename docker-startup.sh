#!/bin/sh

# Ensure persmissions are set correctly
chown -R comics:comics /home/comics/.config /home/comics/.local

# Set up the cronjob and run the cron daemon
logf='/comics-mailer/data/last_run.log'
echo "$CRON date > $logf; /comics-mailer/code/comics_mailer.py >> $logf" | crontab -u comics -
crond

# Keep the container running
tail -f /dev/null

