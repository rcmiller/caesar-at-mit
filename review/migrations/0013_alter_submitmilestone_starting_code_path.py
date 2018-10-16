# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-02-25 18:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0012_remove_reviewmilestone_chunk_priorities'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submitmilestone',
            name='starting_code_path',
            field=models.CharField(blank=True, default=b'', help_text=b'Folder containing starting code for the assignment.  Should contain one subfolder, usually called staff/, under which is the starting code.', max_length=300),
        ),
    ]