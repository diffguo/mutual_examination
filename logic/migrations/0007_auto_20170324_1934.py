# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-24 19:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0006_auto_20170324_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluation',
            name='detail',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='evaluationbak',
            name='detail',
            field=models.CharField(default='', max_length=255),
        ),
    ]