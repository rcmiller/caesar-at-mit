# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Task.due'
        db.alter_column('review_task', 'due', self.gf('django.db.models.fields.DateTimeField')(null=True))


    def backwards(self, orm):
        
        # Changing field 'Task.due'
        db.alter_column('review_task', 'due', self.gf('django.db.models.fields.DateTimeField')(default=None))


    models = {
        'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'assigned_chunks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'reviewers'", 'symmetrical': 'False', 'through': "orm['review.Task']", 'to': "orm['chunks.Chunk']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'chunks.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "u'assignments'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'chunks.chunk': {
            'Meta': {'object_name': 'Chunk', 'db_table': "u'chunks'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.IntegerField', [], {})
        },
        'chunks.file': {
            'Meta': {'unique_together': "(('path', 'submission'),)", 'object_name': 'File', 'db_table': "u'files'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.Submission']"})
        },
        'chunks.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.Assignment']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'review.comment': {
            'Meta': {'ordering': "['start', 'end']", 'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['chunks.Chunk']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_comments'", 'null': 'True', 'to': "orm['review.Comment']"}),
            'start': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'})
        },
        'review.star': {
            'Meta': {'object_name': 'Star'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stars'", 'to': "orm['auth.User']"}),
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stars'", 'to': "orm['chunks.Chunk']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'review.task': {
            'Meta': {'object_name': 'Task'},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['chunks.Chunk']"}),
            'due': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['accounts.UserProfile']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'})
        },
        'review.vote': {
            'Meta': {'unique_together': "(('comment', 'author'),)", 'object_name': 'Vote'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['auth.User']"}),
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['review.Comment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }

    complete_apps = ['review']