#!/bin/sh
kinit -k -t /etc/krb5.keytab host/caesar.csail.mit.edu
aklog athena
/var/django/caesar/preprocessor/takeSnapshots.py --subject 6.031 "$@"
/var/django/caesar/preprocessor/preprocessor.py --subject 6.031 "$@"

