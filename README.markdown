Requirements
============
* Ubuntu or Debian
* Python 2.7 with `pip` available
* Apache 2.4 with `mod_wsgi` and `mod_ssl`

All of the configuration files expect the project code to live at 
`/var/django/caesar`.


Development
============

We use Vagrant and VirtualBox to run Caesar in a virtual machine on your laptop.  Here are the steps:

### Clone from github

Clone this repository from github, if you haven't already.

    git clone https://github.com/uid/caesar-web.git

### Create and start the virtual machine

Install [Vagrant](http://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org) on your laptop.

Make sure you're in your caesar-web folder, which has the Vagrantfile in it.  Start the VM:

    cd caesar-web
    vagrant up

Ignore the final warning from apache2: Could not reliably determine the server's fully qualified domain name.

Log into it:

    vagrant ssh

If it asks you for a password, the password for the vagrant account is just "vagrant".

### Configure local settings

Copy the template for settings_local.py:

    cd /var/django/caesar/caesar
    cp settings_local.py.template settings_local.py

The default settings are intended for development: DEBUG is turned on, a local sqlite database file is used for storing data.

### Collect static files

Collect the static files (CSS, Javascript, images, etc.) from all the apps and libraries used by Caesar into one place where Apache can serve them:

    ./manage.py collectstatic


### Initialize the database

Now, initialize the database.  With the default settings_local.py file, the database is stored in a .sqlite3 file in /home/vagrant, so you can always delete that file and start this part over if things go wrong. 

    cd /var/django/caesar
    ./manage.py migrate

If you want to preload the database with test data do this:

    ./manage.py loaddata fixtures/test_fixtures.json

If you did NOT complete the previous step (preloading the database with test data), create a superuser that will allow you to log in to Caesar with admin privileges:

    ./manage.py createsuperuser


### Test that Caesar is running

Restart the Apache webserver:

    sudo apachectl graceful  # to restart Apache and force it to reload Caesar

Browse to [10.18.6.31](http://10.18.6.31) on your laptop and try to log in, either using the superuser account you created above, or (if you're at MIT) with your MIT certificate.  If login is successful, clicking on the "view all users" link at the top of the page should show you all the users in the test database.


### Development tips

To edit code, work with git, and use other dev tools, just work with the caesar-web folder that you checked out to your laptop.  This folder tree is synced automatically with /var/django/caesar in the VM.  You don't have to go inside the VM.

The only thing you *do* have to do from the VM is restart Apache whenever you edit a Python source file.  Here's how:

    vagrant ssh              # if you're not already logged into your VM
    sudo apachectl graceful  # to restart Apache and force it to reload Caesar

The Django debug toolbar ("DjDt") appears on the right side of Caesar's web pages whenever you have DEBUG=True in settings_local.py.  The toolbar is particularly useful for viewing debug messages. To print messages, use

    import logging
    logging.debug("hello, world")

Messages like this will appear in the Logging pane of the debug toolbar.

To run Caesar in debug mode, use the following command:
    python -m pdb manage.py runserver localhost:8888

This will cause Django to automatically reload all altered code. Additionally, by using:
    import pdb; pdb.set_trace()
you can drop down into a PDB session, which is incredibly useful for debugging crashes & bugs.

By default, your development web server isn't visible outside your laptop.  Nobody else can browse to 10.18.6.31.  But you can make it visible (at your laptop's IP address) using an ssh tunnel:

    sudo ssh -L 0.0.0.0:80:localhost:80 -L 0.0.0.0:443:localhost:443 vagrant@10.18.6.31
    (Default) Password: vagrant


Deployment
==========

These instructions were written for deployment on Ubuntu 14 (Trusty) with Apache 2.4.

### Check out Caesar

Caesar assumes that it will live at `/var/django/caesar`, so create that folder and give yourself ownership of it:

    sudo mkdir -p /var/django/caesar
    sudo chown $USER /var/django/caesar
    sudo chgrp $USER /var/django/caesar

Now check out the code:

    sudo apt-get install -y git  # make sure git is installed
    git clone https://github.com/uid/caesar-web.git /var/django/caesar


### Install Django and other dependencies

Now run the setup script:

    sudo /var/django/caesar/setup.sh


### Create a MySql database

You will need to create a MySql database to run a deployed instance of Caesar.
Either install MySql locally, or make a database on some hosted MySql service.

**Make sure your MySql database has its default character set configured to utf8mb4.**
It's easiest to do it while the database is still fresh and empty.
Use the `mysql` client to visit your database, and run this command:

    alter database character set utf8mb4;


### Configure Caesar

To point Caesar to the right database, copy the local settings file:

    cd /var/django/caesar/caesar
    cp settings_local.py.template settings_local.py

Then edit settings_local.py and change the settings appropriately.

### Collect static files

Collect the static files (CSS, Javascript, images, etc.) from all the apps and libraries used by Caesar into one place where Apache can serve them:
 
    ./manage.py collectstatic

### Initialize the database

Finally, if you are starting a new database, the database needs some setup:

    cd /var/django/caesar
    ./manage.py migrate
    ./manage.py createsuperuser
    sudo apachectl graceful    # restart Apache

Finally browse to your web server and try to log in.


Unicode Support for MySql
==========================

If you are using MySql, you need to make sure that the files and comments tables in the database are using the utf8mb4 character set.
Otherwise you will not be able to have Unicode characters and emojis in source code files or reviewing comments.

To check what the default character set is, use the `mysql` client to visit your database, and run these commands:

    show variables where variable_name = 'character_set_database';
    show full columns from files;
    show full columns from comments;

If you see `utf8mb4` or `utf8mb4_general_ci` for all appropriate character set and collations, then it's correctly configured.
If you see `latin1` or some other character set, your database isn't using Unicode.

To fix the database default:

    alter database character set utf8mb4;

To fix the tables:

    alter table files convert to character set utf8mb4;
    alter table comments convert to character set utf8mb4;
