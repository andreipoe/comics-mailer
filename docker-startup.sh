#!/bin/sh

# Ensure persmissions are set correctly
chown -R comics:comics /home/comics/.config /home/comics/.local

# Check for the setup command
if [ "$1" = 'setup' -o "$1" = '--setup' ]; then
    su -c '/comics-mailer/code/comics_mailer.py --setup' comics
elif [ "$1" = 'run' ]; then
    # Set up the cronjob and run the cron daemon by default
    logf='/comics-mailer/data/last_run.log'
    echo "$CRON date > $logf; /comics-mailer/code/comics_mailer.py >> $logf" | crontab -u comics -
    crond

    # Keep the container running
    tail -f /dev/null
else
    # Handle custom commands otherwise
    exec "$@"
fi

