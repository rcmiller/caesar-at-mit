from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from review.models import *
import datetime

admin.site.unregister(User)
UserAdmin.list_display += ('date_joined', 'last_login',)
UserAdmin.list_filter += ('date_joined', 'last_login',)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]
admin.site.register(User, UserProfileAdmin)

class MemberAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "semester":
            kwargs["queryset"] = Semester.objects.order_by('-is_current_semester','-semester', 'subject__name')
        return super(MemberAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'semester__semester', 'semester__subject__name')
    raw_id_fields = ('user',)
    list_select_related = ('user', 'semester__subject')
admin.site.register(Member, MemberAdmin)

class ExtensionAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "milestone":
            kwargs["queryset"] = Milestone.objects.order_by('-assignment__semester', 'assignment__name', 'name')
        return super(ExtensionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    list_select_related = ('user', 'milestone__assignment__semester__subject')
admin.site.register(Extension, ExtensionAdmin)

class AssignmentAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "semester":
            kwargs["queryset"] = Semester.objects.order_by('-is_current_semester','-semester', 'subject__name')
        return super(AssignmentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    list_display = ('name', 'semester')
    list_select_related = ('semester__subject',)
    search_fields = ('name', 'semester__semester', 'semester__subject__name')
admin.site.register(Assignment, AssignmentAdmin)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__')
    list_select_related = ('milestone__assignment__semester__subject',)
    search_fields = ('authors__username',)
admin.site.register(Submission, SubmissionAdmin)

class ChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file', 'start', 'end')
    list_select_related = ('file',)
    search_fields = ('name', 'file__path', 'file__submission__name')
    raw_id_fields = ('file',)
admin.site.register(Chunk, ChunkAdmin)

class MilestoneAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assignment":
            kwargs["queryset"] = Assignment.objects.order_by('-semester', 'name')
        return super(MilestoneAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    list_select_related = ('assignment__semester__subject',)

class ReviewMilestoneAdmin(MilestoneAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "submit_milestone":
            kwargs["queryset"] = SubmitMilestone.objects.order_by('-assignment__semester', 'assignment__name', 'name')
        return super(ReviewMilestoneAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    list_display = ('id', '__str__',)
    # def routing_link(self, obj):
    #     return mark_safe('<a href="%s%s">%s</a>' % ('/simulate/', obj.id, 'Configure Routing'))
    # routing_link.short_description = 'Configure Routing'
    # def list_users_link(self, obj):
    #     return mark_safe('<a href="%s%s">%s</a>' % ('/list_users/', obj.id, 'List Users'))
    # list_users_link.short_description = 'List Users'
    exclude = ('type',)
admin.site.register(ReviewMilestone, ReviewMilestoneAdmin)

class SubmitMilestoneAdmin(MilestoneAdmin):
    list_display = ('id', '__str__', 'extension_data',)
    list_per_page = 20 # because extension_data involves a couple SQL queries for each line
    def extension_data(self, obj):
        num_no_extensions = Member.objects.filter(semester=obj.assignment.semester, role=Member.STUDENT)\
            .exclude(user__extensions__milestone=obj).count()
        extensions = str(num_no_extensions)
        for num_days in range(1, obj.max_extension+1):
            num_extensions = Extension.objects.filter(milestone=obj).filter(slack_used=num_days).count()
            extensions += ' / ' + str(num_extensions)
        return mark_safe('<a href="%s%s">%s</a>' % ('/all_extensions/', obj.id, extensions))
    extension_data.short_description = 'Extensions (0 Days / 1 Day / 2 Days / ...)'
    exclude = ('type',)
admin.site.register(SubmitMilestone, SubmitMilestoneAdmin)

class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'path')
    search_fields = ('path','submission__authors__username',)
    ordering = ('-id',)
    raw_id_fields = ('submission',)
admin.site.register(File, FileAdmin)

class BatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'milestone_name', 'number_of_submissions', 'loaded_at')
    list_per_page = 20 # because the list involves a couple SQL queries for each line, done by the methods below
    ordering = ('-id', )
    def milestone_name(self, batch):
        milestones = SubmitMilestone.objects.filter(submissions__batch=batch)
        return milestones[0].__str__() if milestones.exists() else None
    def number_of_submissions(self, batch):
        return Submission.objects.filter(batch=batch).count()
    def loaded_at(self, batch):
        submissions = Submission.objects.filter(batch=batch)
        return submissions[0].created if submissions.exists() else None
admin.site.register(Batch, BatchAdmin)

admin.site.register(Subject)
admin.site.register(Semester)

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'reviewer', 'submission', 'chunk')
    list_select_related = ('reviewer', 'submission__milestone__assignment__semester__subject', 'chunk')
    ordering = ('-id',)
    fields = ('chunk', 'submission', 'reviewer', 'status', 'milestone', 'created', 'opened', 'completed',)
    readonly_fields = ('created', 'opened', 'completed')
    search_fields = ('reviewer__username', 'submission__authors__username', 'milestone__assignment__semester__semester', 'milestone__assignment__semester__subject__name','milestone__assignment__name')
    raw_id_fields = ('submission', 'chunk', 'chunk_review', 'reviewer',)
admin.site.register(Task, TaskAdmin)

class VoteInline(admin.TabularInline):
    model = Vote
    raw_id_fields = ('comment', 'author', )
class CommentAdmin(admin.ModelAdmin):
    inlines = [ VoteInline ]
    list_display = ('id', 'chunk', 'start', 'end', 'type', 'author', 'text')
    list_select_related = ('chunk','author')
    ordering = ('-id',)
    search_fields = ('chunk__name', 'text', 'author__username', 
            'author__first_name', 'author__last_name')
    raw_id_fields = ('chunk', 'author', 'batch', 'parent', 'similar_comment')
admin.site.register(Comment, CommentAdmin)
