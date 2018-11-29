from django.conf.urls import url, include
from django.views.generic import RedirectView, TemplateView
import django.contrib.auth.views
import review.views
from django.conf import settings

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    url(r'^dashboard/(?P<username>\w+)', review.views.student_dashboard, name='student_dashboard'),
    url(r'^dashboard/', review.views.dashboard, name='dashboard'),
    url(r'^more_work/', review.views.more_work, name='more_work'),
    url(r'^cancel_assignment/', review.views.cancel_assignment, name='cancel_assignment'),
    url(r'^view/(?P<chunk_id>\d+)', review.views.view_chunk, name='view_chunk'),
    url(r'^submission/(?P<viewtype>(all|code))/(?P<submission_id>\d+)(?P<embedded>/embedded)?', review.views.view_all_chunks, name='all_chunks'),
    url(r'^submission-for-milestone/(?P<viewtype>(all|code))/(?P<milestone_id>\d+)/(?P<username>\w+)', review.views.view_submission_for_milestone, name='for_milestone'),
    url(r'^submissions-for-assignment/(?P<viewtype>(all|code))/(?P<assignment_id>\d+)/(?P<username>\w+)', review.views.view_submissions_for_assignment, name='for_assignment'),
    url(r'^simulate/(?P<review_milestone_id>\d+)', review.views.simulate, name='simulate'),
    url(r'^list_users/(?P<review_milestone_id>\d+)', review.views.list_users, name='list_users'),
    url(r'^load_similar_comments/(?P<chunk_id>\d+)/(?P<load_all_staff_comments>(True|False))', review.views.load_similar_comments, name='similar_comments'),
    url(r'^highlight_comment_chunk_line/(?P<comment_id>\d+)', review.views.highlight_comment_chunk_line, name='chunk_line'),
    url(r'^change_task/', review.views.change_task, name='change_task'),
    url(r'^new_comment/', review.views.new_comment, name='new_comment'),
    url(r'^reply/', review.views.reply, name='reply'),
    url(r'^delete_comment/', review.views.delete_comment, name='delete_comment'),
    url(r'^edit_comment/', review.views.edit_comment, name='edit_comment'),
    url(r'^vote/', review.views.vote, name='vote'),
    url(r'^unvote/', review.views.unvote, name='unvote'),
    url(r'activity/(?P<review_milestone_id>\d+)/(?P<username>\w+)', review.views.all_activity, name='all_activity'),
    url(r'^search/', review.views.search, name='search'),
    url(r'login/', django.contrib.auth.views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'logout/', django.contrib.auth.views.LogoutView.as_view(), name='logout'),
    url(r'register/(?P<email>.+alum\.mit\.edu)/(?P<code>[0-9A-Fa-f]+$)', review.views.register, name='register'),
    url(r'reputation_adj/', review.views.reputation_adjustment, name='reputation_adjustment'),
    url(r'bulk_add/', review.views.bulk_add, name='bulk_add'),
    url(r'^user/(?P<username>\w+)', review.views.view_profile, name='view_profile'),
    url(r'^request_extension/(?P<milestone_id>\d+)', review.views.request_extension, name='request_extension'),
    url(r'^allusers/', review.views.allusers, name='allusers'),
    url(r'^manage/', review.views.manage, name='manage'),
    url(r'^all_extensions/(?P<milestone_id>\d+)', review.views.all_extensions, name='all_extensions'),
]

# from https://github.com/bernardopires/django-tenant-schemas/issues/222
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
