#!/bin/sh

CAESAR_DIR=/var/django/caesar

# Set time zone.
#    **** comment out for now, not sure Caesar needs this
#echo America/New_York > /etc/timezone
#/usr/sbin/dpkg-reconfigure tzdata

# Install Linux packages we need.
apt-get update
apt-get install -y apache2 apache2-dev libapache2-mod-wsgi-py3 # for Apache
apt-get install -y libmysqlclient-dev libldap2-dev libsasl2-dev # MySQL, LDAP
apt-get install -y default-jre # in order to run checkstyle
apt-get install -y python3.7 python3-pip # Django 2.1+ requires Python 3.7+

# Install Python packages we need.
cd /tmp
pip3 install -r $CAESAR_DIR/requirements.txt

# Set up SSL
a2enmod ssl

# Install Caesar into Apache
ln -sf $CAESAR_DIR/apache/caesar.conf /etc/apache2/sites-available
a2ensite caesar

# Start or restart Apache
apachectl graceful
