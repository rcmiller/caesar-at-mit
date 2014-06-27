from django.core import serializers
from django.db.models import Q, Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from  django.core.exceptions import ObjectDoesNotExist

from chunks.models import Chunk, Assignment, Milestone, SubmitMilestone, ReviewMilestone, Submission, StaffMarker
from review.models import Comment, Vote
from tasks.models import Task
from tasks.routing import assign_tasks
from accounts.models import UserProfile, Extension, Member

import datetime
import sys
import logging

@login_required
def dashboard(request):
    user = request.user

    # assign new reviewing tasks to this user
    new_task_count = 0
    allow_requesting_more_tasks = False
    live_review_milestones = ReviewMilestone.objects.filter(assigned_date__lt=datetime.datetime.now(),\
         duedate__gt=datetime.datetime.now(), assignment__semester__members__user=user).all()
    for review_milestone in live_review_milestones:
        current_tasks = user.tasks.filter(milestone=review_milestone)
        active_sub = Submission.objects.filter(authors=user, milestone=review_milestone.submit_milestone)
        try:
            membership = Member.objects.get(user=user, semester=review_milestone.assignment.semester)
            if active_sub.count() or not Member.STUDENT in membership.role:
                #logging.debug("I can have assignments")
                # user is a student with an existing submission, or isn't a student
                # allow user to request more tasks manually
                allow_requesting_more_tasks = True
                if not current_tasks.count():
                    # automatically assign new tasks to student ONLY if they don't already have tasks
                    #logging.debug("assigning tasks")
                    new_task_count += assign_tasks(review_milestone, user)
        except ObjectDoesNotExist:
            pass

    return dashboard_for(request, user, new_task_count)

@staff_member_required
def student_dashboard(request, username):
    try:
        other_user = User.objects.get(username=username)
    except:
        raise Http404
    return dashboard_for(request, other_user)

def dashboard_for(request, dashboard_user, new_task_count = 0, allow_requesting_more_tasks = False):
    def annotate_tasks_with_counts(tasks):
        return tasks.annotate(comment_count=Count('chunk__comments', distinct=True),
                       reviewer_count=Count('chunk__tasks', distinct=True))
        #logging.log(tasks.all()[0].comment_count)

    all_tasks = dashboard_user.tasks \
        .select_related('submission', 'chunk__file__submission__milestone', 'milestone__assignment__semester__subject')
    active_tasks = all_tasks \
        .exclude(status='C') \
        .exclude(status='U') \
        .order_by('chunk__name', 'submission__name')
    active_tasks = annotate_tasks_with_counts(active_tasks)

    old_completed_tasks = all_tasks \
        .filter(status='C') \
        .exclude(chunk__file__submission__milestone__assignment__semester__is_current_semester=True)
    old_completed_tasks = annotate_tasks_with_counts(old_completed_tasks)

    completed_tasks = all_tasks \
        .filter(status='C') \
        .filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True) \
        .order_by('completed').reverse()
    completed_tasks = annotate_tasks_with_counts(completed_tasks)

    '''
    Gathers data from submissions of a user, including comments and number of reviewers on those submissions.
    @attr - submissions - QuerySet of submissions.
    '''
    def collect_submission_data(submissions):
        data = []
        for submission in submissions:
            user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
            static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
            reviewer_count = User.objects.filter(tasks__chunk__file__submission = submission).count()
            data.append((submission, reviewer_count, submission.last_modified,
                                      user_comments, static_comments))
        return data

    '''
    Returns a list of tuples in the form (user-generated comment, comment creation time, list_as_reply=False)
    (NOT A LIST OF LISTS) for all submissions of a user. The first entry in the list is the earliest comment,
    and the last entry is the latest comment.
    Note to dev: list_as_reply is used for icons in the template, since the sorting method
    will lose track of what comments are replies to users code, not necessarily on one of their own submissions.
    @param - submissions - QuerySet of submissions.
    '''
    def collect_comments_from_submissions(submissions):
        all_comments = []
        for submission in submissions:
            user_code_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U')
            for comment in user_code_comments:  #this is done to have a list of comments instead of a list of lists.
                all_comments.append((comment, comment.created, False))
        return all_comments

    '''
    Returns a list of tuples in the form of (reply, reply.created, list_as_reply=True) where reply is a comment that is a child
    to a parent comment created by the dashboard user.
    @param - submissions - QuerySet of submissions.
    '''
    def collect_replies_to_user(submissions):
        replies = []
        for submission in submissions:
            submission_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U')
            for comment in submission_comments:
                if comment.parent is not None:
                    if comment.parent.author == dashboard_user:
                        #NOTE: remember to use the version with this being True if a duplicate appears
                        replies.append((comment, comment.created, True))
        return replies

    '''
    Returns a list of comments with recent vote activity, with the comment with the most recent
    vote activity at the end of the list.
    @param - submisssions - QuerySet of submissions.
    '''
    def collect_recent_votes():
        votes_tuple_list = []
        votes_on_user = Vote.objects.filter(comment__author=dashboard_user)
        for vote in votes_on_user:
            votes_tuple_list.append((vote, vote.modified))
        return votes_tuple_list

    '''
    Returns a sorted list all of the list arguments by their time of modification or creation, depending on the object,
    where the 0 index is used for the earliest action. (votes use modification time, comments use creation time)
    @param comments_list - list generated from collect_comments_from_submissions
    @param replies_list - list generated from collect_replies_to_user
    @param comments_from_vote_list - list generated from collect_recent_votes
    '''
    def create_recent_activity_list(comments_list, replies_list, votes_list):
        list_of_lists = [comments_list, replies_list, votes_list]

        #list comp. flattens list_of_lists
        #(see http://stackoverflow.com/questions/716477/join-list-of-lists-in-python)
        recent_activity_tuple = [inner for outer in list_of_lists for inner in outer]

        #sorts the list by the time entry in the second position of each tuple.
        recent_activity_tuple.sort(key = lambda object_time_tuple: object_time_tuple[1])

        #recent_activity contains 'Comment tuples' and Vote objects, where the last item is the
        #most recent item that should appear at the top in recent activity in the template.
        #Comment tuples are tuples in form (Comment, boolean), where the boolean will be
        #read in the template to decide if the comment is a reply to a user comment
        #or a comment on a users submission.
        #(if len(i) < 3, it's a vote object, so just gather the vote itself.)
        recent_activity = [i[0] if len(i) < 3 else (i[0], i[2]) for i in recent_activity_tuple]
        return recent_activity


    #get all the submissions that the user submitted
    submissions = Submission.objects.filter(authors=dashboard_user) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .filter(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    all_submissions = Submission.objects.all()

    submission_data = collect_submission_data(submissions)
    #TODO: make sure this isn't too time intensive.
    submission_comments = collect_comments_from_submissions(submissions) #TODO: maybe expand this into old_submission_data too
    submission_replies = collect_replies_to_user(all_submissions)
    submission_voted_recently = collect_recent_votes()
    recent_activity_objects = create_recent_activity_list(submission_comments, submission_replies, submission_voted_recently)

    #get all the submissions that the user submitted, in previous semesters
    old_submissions = Submission.objects.filter(authors=dashboard_user) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .exclude(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    old_submission_data = collect_submission_data(old_submissions)

    #find the current submissions
    current_milestones = SubmitMilestone.objects.filter(assignment__semester__members__user=dashboard_user, assignment__semester__members__role=Member.STUDENT)\
        .filter(assigned_date__lt= datetime.datetime.now())\
        .order_by('duedate')

    current_milestone_data = []
    for milestone in current_milestones:
        try:
            user_extension = milestone.extensions.get(user=dashboard_user)
            extension_days = user_extension.slack_used
        except ObjectDoesNotExist:
            user_extension = None
            extension_days = 0
        if datetime.datetime.now() <= milestone.duedate + datetime.timedelta(days=extension_days) + datetime.timedelta(hours=2):
            current_milestone_data.append((milestone, user_extension))

    #find total slack days left for each membership
    current_memberships = Member.objects.filter(user=dashboard_user)

    current_slack_data = []
    for membership in current_memberships:
            total_slack = membership.slack_budget
            used_slack = sum([extension.slack_used for extension in Extension.objects.filter(user=dashboard_user, milestone__assignment__semester=membership.semester)])
            slack_left = total_slack - used_slack
            current_slack_data.append((membership.semester, slack_left))


    return render(request, 'dashboard/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_milestone_data': current_milestone_data,
        'allow_requesting_more_tasks': allow_requesting_more_tasks,
        'recent_activity_objects': recent_activity_objects,
        'current_slack_data': current_slack_data,
    })