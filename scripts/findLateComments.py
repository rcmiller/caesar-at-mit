#!/usr/bin/env python3
import sys, os, django

# set up Django
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from review.models import *

import argparse
parser = argparse.ArgumentParser(description="""
Prints comments made after a review milestone's reveal date.
""")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of ReviewMilestone in Caesar. Go to Admin, ReviewMilestone, and take the last number from the link.")


args = parser.parse_args()

review_milestone = ReviewMilestone.objects.get(id=args.milestone)
submit_milestone = review_milestone.submit_milestone
late_comments = Comment.objects.filter(chunk__file__submission__milestone=review_milestone.submit_milestone, created__gt=review_milestone.reveal_date)

for comment in late_comments:
    code_authors = comment.chunk.file.submission.authors.all()
    commenter = comment.author
    if commenter not in code_authors:
        print("-".join([user.username for user in code_authors]), "received a late comment from", commenter, '"' + str(comment) + '"')
