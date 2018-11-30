#!/usr/bin/env python2.7
import sys, os, argparse, django

# set up Django
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caesar.settings")
django.setup()

from django.db.models import Q
from django.contrib.auth.models import User
from review.models import UserProfile, Member, Chunk, Assignment, Submission, Subject, Semester

import ldap
import ldap.filter

from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist

# create from a list of usernames
def loadusers(filename, role, semester, extension_days):
    f = open(filename)
    for line in f:
        username = line.split()[0]
        makeuser(username, role, semester, extension_days)

# create a single user
def makeuser(username, role, semester, extension_days):
    print(username)
    user, user_created  = User.objects.get_or_create(username=username, is_active=True)
    if user_created:
        fetch_user_data_from_LDAP(user)
        user.save()

    member, created = Member.objects.get_or_create(user=user, semester=semester, slack_budget=extension_days)
    if not created:
        print "...already a " + member.get_role_display() + " member"
    else:
        if role == "student":
            member.role = Member.STUDENT
        elif role == "teacher":
            member.role = Member.TEACHER
        elif role == "volunteer":
            member.role = Member.VOLUNTEER
    member.save()

def fetch_user_data_from_LDAP(user, ):
    username = user.username
    user.set_unusable_password()
    con = ldap.open('ldap.mit.edu')
    con.simple_bind_s("", "")
    dn = "dc=mit,dc=edu"
    fields = ['cn', 'sn', 'givenName', 'mail', ]
    userfilter = ldap.filter.filter_format('uid=%s', [username])
    result = con.search_s('dc=mit,dc=edu', ldap.SCOPE_SUBTREE, userfilter, fields)
    print(result)
    if len(result) == 1:
        data = result[0][1]
        if 'givenName' in data:
            user.first_name = data['givenName'][0] 
        if 'sn' in data:
            user.last_name = data['sn'][0]
        if 'mail' in data:
            user.email = data['mail'][0]
        user.save()
        user.profile.company = 'MIT'
        user.profile.save()
    else:
        raise ValueError("Could not find user with username '%s' (filter '%s')"%(username, userfilter))
    return user

#gets a list of all student emails, outputs to 'student_emails.txt'
def student_email(semester):
    f = open('student_emails.txt', 'w')
    students = Member.objects.filter(role=Member.STUDENT, semester=semester)
    for s in students:
      f.write(s.user.email + "\n")
    f.close()

#get all student usernames
def students(semester):
    students = Member.objects.filter(role=Member.STUDENT, semester=semester).membership
    for s in students:
      print(s.user.username)
    

parser = argparse.ArgumentParser(description="""
Make users into members of a class (as either students or staff).
Also creates user accounts for any who don't already have a Caesar account.
""")
parser.add_argument('--subject',
                    nargs=1,
                    type=str,
                    required=True,
                    help="name of Subject (in caesar.eecs.mit.edu/admin/subject/; for example '6.005'")
parser.add_argument('--semester',
                    nargs=1,
                    type=str,
                    required=True,
                    help="name of Semester (in caesar.eecs.mit.edu/admin/semester/; for example 'Fall 2013')")
parser.add_argument('--role',
                    nargs=1,
                    type=str,
                    choices=[role[1] for role in Member.ROLE_CHOICES],
                    default=["student"],
                    help="role of these users in the class")
parser.add_argument('--slackbudget',
                    nargs=1,
                    type=int,
                    default=[10],
                    help="number of days of slack to give to students")
parser.add_argument('--file',
                    nargs=1,
                    type=str,
                    help="filename containing Athena usernames")
parser.add_argument('usernames',
                    nargs='*',
                    help="Athena usernames of students or staff")


args = parser.parse_args()
#print(args)

subject = Subject.objects.get(name=args.subject[0])
semester = Semester.objects.get(subject=subject, semester=args.semester[0])

role=args.role[0]
slackbudget=args.slackbudget[0]

if role!="student":
    slackbudget=0 # only students need slack

if args.file:
    loadusers(args.file[0], role, semester, slackbudget)

for username in args.usernames:
    makeuser(username, role, semester, slackbudget)
