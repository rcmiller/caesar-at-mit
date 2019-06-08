#!/bin/sh

CAESAR_DIR=/var/django/caesar

# Set time zone.
#    **** comment out for now, not sure Caesar needs this
#echo America/New_York > /etc/timezone
#/usr/sbin/dpkg-reconfigure tzdata

# This part is needed by OpenStack VM:
# display progress of Ubuntu unattended-upgrade
# (since it is typically running right after the VM instance is launched)
# https://askubuntu.com/questions/934807/unattended-upgrades-status
tail -f /var/log/unattended-upgrades/unattended-upgrades.log &

# and wait for unattended-upgrades to finish
# https://unix.stackexchange.com/questions/463498/terminate-and-disable-remove-unattended-upgrade-before-command-returns
sudo systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait /bin/true

# Install Linux packages we need.
sudo apt-get update
#sudo apt-get upgrade
sudo apt-get install -y apache2 apache2-dev libapache2-mod-wsgi-py3 # for Apache
sudo apt-get install -y sqlite3 # for development
sudo apt-get install -y libmysqlclient-dev libldap2-dev libsasl2-dev # MySQL, LDAP
sudo apt-get install -y default-jre # in order to run checkstyle
sudo apt-get install -y python3.7 python3-pip # Django 2.1+ requires Python 3.7+

# Install Python packages we need.
cd /tmp
sudo -H pip3 install -r $CAESAR_DIR/requirements.txt

# Set up SSL
sudo a2enmod ssl

# Install Caesar into Apache
sudo ln -sf $CAESAR_DIR/apache/caesar.conf /etc/apache2/sites-available
sudo a2ensite caesar

# Start or restart Apache
sudo apachectl graceful

# Collect static files for Apache to server
cd $CAESAR_DIR
./manage.py collectstatic --link --noinput

