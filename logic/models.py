#coding=utf-8
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class TCorpWeixinToken(models.Model):
    accesstoken = models.CharField(max_length=600)
    expiresdatetime = models.DateTimeField()

class UserProfile(models.Model):
    corpweixinid = models.CharField(max_length=10, unique=True) # ok
    username = models.CharField(max_length=20)
    isleader = models.BooleanField(default=False)
    scoreproportion = models.FloatField(default=0.25) # 最后计算分数时leader的占比
    superiorid = models.CharField(max_length=10, default="")
    superiorname = models.CharField(max_length=30, default="")
    department = models.CharField(max_length=20)
    position = models.CharField(max_length=30)
    mobile = models.CharField(max_length=20)
    email = models.CharField(max_length=40)
    gender = models.CharField(max_length=1)
    avatar = models.CharField(max_length=256)
    enable = models.BooleanField(default=True)
    updatetime = models.DateTimeField(auto_now=True)
    createtime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'

#考核数据流转： 1. 调用init接口，补充UserProfile；清理Evaluation表；2. 开始邀请人到邀请表，并等待确认；3. 确认后进入Evaluation表。 4。 所有人打分完成后开始计算分数，并计入FinalScore
class BeEvaluation(models.Model):
    BE_EVA_STATE_CHOICE=((0,u'新建'),(1,u'待审核'),(2,u'待考核'),(3,u'考核完成'),)

    quarter = models.CharField(max_length=8)
    corpweixinid = models.CharField(max_length=10, db_index=True) # ok
    name = models.CharField(max_length=20, default='')
    superiorid = models.CharField(max_length=10, default='', db_index=True)
    assessors = models.TextField()# 被邀请者列表，包含名称
    state = models.SmallIntegerField(choices=BE_EVA_STATE_CHOICE, default=0)
    updatetime = models.DateTimeField(auto_now=True)
    createtime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quarter', 'corpweixinid')

# 不分季度，开始考核时，需要清理该表
class Evaluation(models.Model):
    quarter = models.CharField(max_length=8)
    corpweixinid = models.CharField(max_length=10)# 待考核者
    name = models.CharField(max_length=20, default='')
    assessorid = models.CharField(max_length=10, db_index=True)# 打分者 ok
    rawsocre = models.FloatField(default=0)# 直接打分（未计算的分数）
    scorekeepin = models.BooleanField(default=True, db_index=True)# 打分确认状态（有的人的打分需要领导确认，当该值为True才能计算）
    socre = models.FloatField(default=0)# 计算后的分数
    detail = models.CharField(max_length=255, default='')# 详细打分情况[[id,score],[id,score],[id,score]]
    updatetime = models.DateTimeField(auto_now=True)
    createtime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quarter', 'corpweixinid', 'assessorid')

class EvaluationBak(models.Model):
    quarter = models.CharField(max_length=8)
    corpweixinid = models.CharField(max_length=10)# 待考核者
    name = models.CharField(max_length=20, default='')
    assessorid = models.CharField(max_length=10, db_index=True)# 打分者 ok
    rawsocre = models.FloatField(default=0)# 直接打分（未计算的分数）
    scorekeepin = models.BooleanField(default=True, db_index=True)# 打分确认状态（有的人的打分需要领导确认，当该值为True才能计算）
    socre = models.FloatField(default=0)# 计算后的分数
    detail = models.CharField(max_length=255, default='')# 详细打分情况[[id,score],[id,score],[id,score]]
    updatetime = models.DateTimeField(auto_now=True)
    createtime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quarter', 'corpweixinid', 'assessorid')

class QuarterScore(models.Model):
    quarter = models.CharField(max_length=8)
    corpweixinid = models.CharField(max_length=10)
    name = models.CharField(max_length=20)
    socre = models.FloatField()
    updatetime = models.DateTimeField(auto_now=True)
    createtime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quarter', 'corpweixinid')

class YearScore(models.Model):
    LEVEL_CHOICE=(('A',u'等级A'),('B',u'等级B'),('C',u'等级C'),('D',u'等级D'),)

    year = models.CharField(max_length=4)
    corpweixinid = models.CharField(max_length=10)
    name = models.CharField(max_length=20)
    socre = models.FloatField()
    level = models.CharField(max_length=1, choices=LEVEL_CHOICE)
    updatetime = models.DateTimeField(auto_now=True)
    createtime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('year', 'corpweixinid')


    