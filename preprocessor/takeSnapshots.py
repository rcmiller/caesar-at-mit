#!/usr/bin/env python3
import sys, os, argparse, django, re, datetime, itertools, json, csv
from pprint import pprint

# set up Django
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
from django.conf import settings

ROOT='/var/django/caesar/preprocessor'

from review.models import *
from get_milestone import get_milestone

parser = argparse.ArgumentParser(description="""
Snapshots student git repositories on Athena.
""")
parser.add_argument('--subject',
                    nargs=1,
                    type=str,
                    help="name of Subject; for example '6.005'")
parser.add_argument('--semester',
                    nargs=1,
                    type=str,
                    help="name of Semester; for example 'Fall 2013'); if omitted, uses the semester with the latest milestones")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    help="id number of SubmitMilestone; if omitted, uses the latest milestone whose deadline has passed.")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- snapshot the code into the filesystem, but don't save anything into the Caesar database")
parser.add_argument('usernames',
                    nargs='*',
                    help="Athena usernames of students (or dash-separated usernames, for project groups) to load (with optional ':revision' appended to each with the commit that should be used for that student); if omitted, uses all the students in the latest sweep for the milestone.")


args = parser.parse_args()
#print(args)

milestone = get_milestone(args)
print("taking snapshots of code for milestone", str(milestone))

semester = milestone.assignment.semester
semester_name = semester.semester
subject_name = semester.subject.name

force_revision_for_username = {}
restrict_to_usernames = set()
for username in args.usernames:
    if ':' in username:
        (username, revision) = username.split(':')
        force_revision_for_username[username] = revision
    restrict_to_usernames.add(username)
# pprint(force_revision_for_username)
# pprint(restrict_to_usernames)

# convert e.g. Spring 2017 to sp17
m = re.match('(Fa|Sp)\w+ \d\d(\d\d)', semester_name)
if m == None:
    print("semester name doesn't follow Season Year format:", semester_name)
    exit(-1)
semester_abbr = m.group(1).lower() + m.group(2)

if args.milestone:
    milestone = SubmitMilestone.objects.get(id=args.milestone)
else:
    milestones = SubmitMilestone.objects.filter(\
        duedate__lte=datetime.datetime.now())\
        .order_by('-duedate')
    if len(milestones) == 0:
        print(subject, semester, "has no submit milestones that have passed")
        exit(-1)
    else:
        milestone = milestones[0]

pset = milestone.assignment.name # e.g. "ps0"
milestone_name = milestone.name # e.g. "beta"
print("updating snapshots for milestone", milestone.full_name())


# take a snapshot from a git repo:string of revision:string and store it at target_path:string 
# if repo is a folder path, uses git archive
# if repo is a url of the form "https://github.mit.edu/owner/repo URL", uses Github API 
def git_snapshot(repo, revision, target_path, snapshot_even_if_already_exists=False):
    if os.path.isdir(target_path):
        if not snapshot_even_if_already_exists:
            return
    else:
        os.makedirs(target_path)
    m = re.match(r'^https://github\.mit\.edu/(.*)$', repo)
    if m:
        # see docs at https://octokit.github.io/rest.js/#api-Repos-getArchiveLink
        ownerAndRepo = m.group(1)
        command = 'curl -s -L -u "{accessToken}" "http://github.mit.edu/api/v3/repos/{ownerAndRepo}/tarball/{revision}"  | tar xz -C "{target_path}" --strip-components 1'.format(accessToken=settings.GITHUB_TOKEN, ownerAndRepo=ownerAndRepo, revision=revision, target_path=target_path)
    else:
        command = 'git --git-dir="{repo}" archive "{revision}" | tar x -C "{target_path}"'.format(repo=repo, revision=revision, target_path=target_path)
    print(command)
    os.system(command)


# equivalent to ln -sf target source
def symlink_force(target, source):
    os.remove(source) if os.path.lexists(source) else None
    os.symlink(target, source)


# in the code below,
# RevisionMap is a dictionary mapping
#   username:string -> revision:string, a revision hash in username's git repo for this pset

# return RevisionMap found in Didit milestone file
def load_revisions():
    # milestone is stored as a CSV file in private/<semester>/code/<pset>/<pset>-<milestone>.csv
    milestone_filename = os.path.join(ROOT, subject_name, 'private', semester_abbr, 'code', pset, pset + "-" + milestone_name + '.csv')

    # milestone CSV file format:
    #   - has a header row
    #   - first column is username, e.g. rcm
    #   - second column is ="revision", e.g. ="e232523"
    #   - additional columns which are ignored by this script
    with open(milestone_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader) # skip header row
        revision_map = {}
        for row in reader:
            username = row[0]
            revision = re.sub(r'^="(.*)"$', r'\1', row[1]) # remove ="..." around the revision hash
            if len(restrict_to_usernames) == 0 or username in restrict_to_usernames:
                revision_map[username] = revision
    return revision_map

# revision_map: RevisionMap
# extracts a snapshot of each user's revision from their git repo (if that snapshot doesn't already exist),
# and makes a symlink to it in the right place 
def snapshot_revisions(revision_map):
    # starting code in (e.g.) https://github.mit.edu/6031-fa18/ps0
    # student code in (e.g.) https://github.mit.edu/6031-fa18/ps0-username

    repos_url = 'https://github.mit.edu/' + subject_name.replace('.', '') + '-' + semester_abbr + '/' + pset
    #print 'repos_url', repos_url

    # snapshots of code will be stored under code_path folder
    code_path = os.path.join(ROOT, subject_name, 'private', semester_abbr, 'code', pset)
    snapshots_path = os.path.join(code_path, "snapshots")
    milestone_path = os.path.join(code_path, milestone_name)

    # make parent folders in case they don't exist yet
    [os.makedirs(path) for path in (snapshots_path, milestone_path) if not os.path.isdir(path)]

    # snapshot the starting code in case it hasn't been done yet
    starting_repo_path = repos_url
    git_snapshot(starting_repo_path, 'HEAD', os.path.join(code_path, 'starting/staff'))

    for username in revision_map.keys():
        revision = revision_map[username]
        snapshot_name = username + "-" + revision
        #print(snapshot_name)
        
        # old repo: user_repo = os.path.join(repos_path, username + '.git')
        user_repo = repos_url + '-' + username
        user_snapshot = os.path.join(code_path, "snapshots", snapshot_name)
        git_snapshot(user_repo, revision, user_snapshot)
        symlink_force(os.path.join('../snapshots', snapshot_name), os.path.join(milestone_path, username))

revision_map = load_revisions()
print("selected revisions for", len(revision_map), "users")
pprint(revision_map)
snapshot_revisions(revision_map)
