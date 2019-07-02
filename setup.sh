#!/bin/sh

CAESAR_DIR=/var/django/caesar

# Set time zone.
#    **** comment out for now, not sure Caesar needs this
#echo America/New_York > /etc/timezone
#/usr/sbin/dpkg-reconfigure tzdata

# This part is needed by OpenStack VM:
# https://unix.stackexchange.com/questions/463498/terminate-and-disable-remove-unattended-upgrade-before-command-returns
echo waiting for unattended upgrades to finish
sudo systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait /bin/true

# Install Linux packages we need.
# The combination of DEBIAN_FRONTEND=noninteractive and -y ensure that we say Yes
# to every prompt, rather than stopping to prompt for user input.
sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

#sudo apt-get upgrade
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y apache2 apache2-dev libapache2-mod-wsgi-py3 # for Apache
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 # for development
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y libmysqlclient-dev libldap2-dev libsasl2-dev # MySQL, LDAP
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y default-jre # in order to run checkstyle
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.7 python3-pip # Django 2.1+ requires Python 3.7+

# Install Python packages we need.
# sudo -H ensures that pip3 uses root's home folder for its cache, rather than
# filling ubuntu's home folder cache with root-owned files.
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

