# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-22 19:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0002_auto_20170322_1442'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='evaluation',
            unique_together=set([('quarter', 'corpweixinid', 'assessorid')]),
        ),
    ]
