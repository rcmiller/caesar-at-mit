#!/usr/bin/env python2.7
import sys, os, argparse, django, re, datetime, itertools, json, csv
from pprint import pprint

# set up Django
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caesar.settings")
django.setup()

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
parser.add_argument('--project',
                    action='store_true',
                    help="this milestone is a group project, not an individual problem set")
parser.add_argument('usernames',
                    nargs='*',
                    help="Athena usernames of students to load (with optional ':revision' appended to each with the commit that should be used for that student); if omitted, uses all the students in the latest sweep for the milestone.")


args = parser.parse_args()
#print args

milestone = get_milestone(args)
print "taking snapshots of code for milestone", str(milestone)

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
print "updating snapshots for milestone", milestone.full_name()



# take a snapshot from a git repo:string of revision:string and store it at target_path:string 
def git_snapshot(repo, revision, target_path, snapshot_even_if_already_exists=False):
    if os.path.isdir(target_path):
        if not snapshot_even_if_already_exists:
            return
    else:
        os.makedirs(target_path)
    command = 'git --git-dir="{repo}" archive "{revision}" | tar x -C "{target_path}"'.format(repo=repo, revision=revision, target_path=target_path)
    print command
    os.system(command)

# for Github API, use
#  https://octokit.github.io/rest.js/#api-Repos-getArchiveLink
# https://github.mit.edu/6031-fa18
# starting code in https://github.mit.edu/6031-fa18/ps0
# student code in https://github.mit.edu/6031-fa18/ps0-username

if args.project:
    def snapshot_projects():
        repos_path = os.path.join(ROOT, subject_name, 'git', semester_abbr, 'projects', pset)
        groups = set([os.path.splitext(filename)[0] for filename in os.listdir(repos_path)])
        if len(restrict_to_usernames) > 0:
            groups = groups.intersection(restrict_to_usernames)
        if 'didit' in groups:
            groups.remove('didit')
        #print groups

        code_path = os.path.join(ROOT, subject_name, 'private', semester_abbr, 'code', pset)
        milestone_path = os.path.join(code_path, milestone_name)

        # make parent folders in case they don't exist yet
        if not os.path.isdir(milestone_name):
            os.makedirs(milestone_name)

        # snapshot the starting code in case it hasn't been done yet
        git_snapshot(os.path.join(repos_path, 'didit/starting.git'), 'HEAD', os.path.join(code_path, 'starting/staff'))

        for group in groups:
            group_repo = os.path.join(repos_path, group + '.git')
            group_snapshot = os.path.join(milestone_path, group)
            git_snapshot(group_repo, 'HEAD', group_snapshot, True)

    snapshot_projects()


else:
    # determine the correct revision to snapshot for each username

    # in the code below,
    # RevisionMap is a dictionary mapping
    #   username:string -> revision:string, a revision hash in username's git repo for this pset


    # deadline: datetime, max_extension: int, number of days of slack allowed on this deadline
    # returns list of RevisionMaps of length max_extension+1, 
    #    where sweeps[i] is the i-days-late RevisionMap, or None if no sweep found for that day
    def find_sweeps(deadline, max_extension):
        old_sweeps_path = os.path.join(ROOT, subject_name, 'didit', semester_abbr, 'sweeps/psets', pset)

        if os.path.exists(old_sweeps_path):
            # old Didit: sweeps were stored in JSON files in didit/<semester>/sweeps/psets/<pset>/<yymmddThhmmss>/sweep.json
            sweep_filenames = os.listdir(old_sweeps_path)

            # sweep file for new didit will be
            #  [header row]
            #  dash-separated-usernames,sha,... (possibly additional columns)

            # filename:string, sweeps folder name, assumed to have the form yymmddThhmmss, e.g. '20170122T221500';
            # returns int, number of days after deadline
            def days_after_deadline(filename):
                return (datetime.datetime.strptime(filename, '%Y%m%dT%H%M%S') - deadline).days

            # choose the first sweep in each 1-day window
            # make sure we look at them in increasing chron order, since os.listdir() makes no order guarantee
            sweep_filenames.sort()
            sweep_filename_for_days_late = [None] * (max_extension + 1)
            for days_late, group in itertools.groupby(sweep_filenames, days_after_deadline):
                if days_late >= 0 and days_late <= max_extension:
                    sweep_filename_for_days_late[days_late] = list(group)[0]

            # filename: string, sweeps foldername under sweeps_path
            # returns RevisionMap of that sweep
            def load_json_sweep(filename):
                with open(os.path.join(sweeps_path, filename, 'sweep.json'), 'r') as f:
                    data = json.load(f)
                    sweep = {}
                    for entry in data['reporevs']:
                        for user in entry['users']:
                            sweep[user] = entry['rev']
                    return sweep
            return [load_json_sweep(filename) if filename else None for filename in sweep_filename_for_days_late]
        else:
            # new Didit: sweeps are stored in CSV files in didit/<semester>/revisions/psets/<pset>/<milestone>/[012].csv
            new_sweeps_path = os.path.join(ROOT, subject_name, 'didit', semester_abbr, 'revisions/psets', pset, milestone_name)

            # filename: string, sweep CSV file with header row and username as first column, revision as second column
            #    (and possibly additional columns which are ignored)
            # returns RevisionMap loaded from that file
            def load_csv_sweep(filename):
                try:
                    with open(filename, 'r') as f:
                        reader = csv.reader(f)
                        reader.next() # skip header row
                        sweep = {}
                        for row in reader:
                            username = row[0]
                            revision = row[1]
                            sweep[username] = revision
                    return sweep
                except IOError:
                    return None
            return [load_csv_sweep(os.path.join(new_sweeps_path, str(days_late) + ".csv")) for days_late in range(0, max_extension+1)]


    # get the RevisionMap for each deadline
    sweeps = find_sweeps(milestone.duedate, milestone.max_extension)
    print "found sweeps for", [i for i in range(0,len(sweeps)) if sweeps[i]], "days late"
    #pprint(sweeps)
    # now sweep[n] is the RevisionMap for n days late (which may be None, if haven't done the n-day sweep yet)



    # sweeps: list of max_extension+1 RevisionMaps, where sweeps[n] is the RevisionMap for n-days-late
    # returns a new RevisionMap for every registered student whose deadline has passed, selecting the n-days-late revision
    #     for that student if the student requested n days of slack
    def select_revisions(sweeps):
        revisions_by_username = {}
        usernames_to_select = set([username for sweep in sweeps if sweep for username in sweep.keys()])
        #pprint(usernames_to_select)
        if len(restrict_to_usernames) > 0:
            usernames_to_select = usernames_to_select.intersection(restrict_to_usernames)
        #pprint(usernames_to_select)

        for username in usernames_to_select:
            if username in force_revision_for_username:
                revisions_by_username[username] = force_revision_for_username[username]
                continue
            if not Member.objects.filter(semester=semester, user__username=username, role=Member.STUDENT).exists():
                print username, "found in sweep but not a student, ignoring"
                continue
            try:
                extension = Extension.objects.get(user__username=username, milestone=milestone)
                sweep_to_use = extension.slack_used
            except Extension.DoesNotExist:
                pass # this is normal; users who didn't request slack have no Extension object
                sweep_to_use = 0 # assume no extension unless we discover otherwise
            if sweeps[sweep_to_use] and username in sweeps[sweep_to_use]:
                revisions_by_username[username] = sweeps[sweep_to_use][username]
        return revisions_by_username

    revision_map = select_revisions(sweeps)
    print "selected revisions for", len(revision_map), "users whose personal deadlines have passed"
    pprint(revision_map)

    # equivalent to ln -sf target source
    def symlink_force(target, source):
        os.remove(source) if os.path.lexists(source) else None
        os.symlink(target, source)

    # revision_map: RevisionMap
    # extracts a snapshot of each user's revision from their git repo (if that snapshot doesn't already exist),
    # and makes a symlink to it in the right place 
    def snapshot_revisions(revision_map):
        repos_path = os.path.join(ROOT, subject_name, 'git', semester_abbr, 'psets', pset)
        code_path = os.path.join(ROOT, subject_name, 'private', semester_abbr, 'code', pset)
        snapshots_path = os.path.join(code_path, "snapshots")
        milestone_path = os.path.join(code_path, milestone_name)

        # make parent folders in case they don't exist yet
        [os.makedirs(path) for path in (snapshots_path, milestone_path) if not os.path.isdir(path)]

        # snapshot the starting code in case it hasn't been done yet
        git_snapshot(os.path.join(repos_path, 'didit/starting.git'), 'HEAD', os.path.join(code_path, 'starting/staff'))

        for username in revision_map.keys():
            revision = revision_map[username]
            snapshot_name = username + "-" + revision
            print snapshot_name
            user_repo = os.path.join(repos_path, username + '.git')
            user_snapshot = os.path.join(code_path, "snapshots", snapshot_name)
            git_snapshot(user_repo, revision, user_snapshot)
            symlink_force(os.path.join('../snapshots', snapshot_name), os.path.join(milestone_path, username))

    snapshot_revisions(revision_map)
