#coding=utf-8
import json
import numpy
import requests
import datetime
from mutual_examination.settings import log
from tools import get_quarter_name,add_superiorid_into_assessors
from score_by_rank import CalcScoreListByRawScoreList
from corpwx_api_tools import get_corp_weixin_token,send_corpweixin_msg
from logic.models import UserProfile,BeEvaluation,Evaluation,QuarterScore
from django.shortcuts import render_to_response
from django.http import HttpResponse,HttpResponseRedirect

def userinfo(request):
    if request.method != "GET":
        return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

    log.info("User Login, corp corpweixinid: %s" % request.user_id)

    users = UserProfile.objects.filter(corpweixinid=request.user_id)
    if not users:
        log.error("Wrong corp corpweixinid: %s" % request.user_id)
        return HttpResponse(json.dumps({"errmsg":"wrong corpweixinid","errcode":1}))

    user = users[0]
    userinfostr = {"userid":request.user_id, "username":user.username, 'isleader':user.isleader, 'avatar':user.avatar}

    return HttpResponse(json.dumps({"userinfo":userinfostr,"errmsg":"","errcode":0}))

user_list = []
last_cache_user_list_time = datetime.datetime.now()
def department_user_list(request):
    global user_list, last_cache_user_list_time
    if request.method != "GET":
        return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))
    
    if (datetime.datetime.now() - last_cache_user_list_time).days >= 1:
        last_cache_user_list_time = datetime.datetime.now()
        user_list = []

    if not user_list:
        tmp_user_list = []
        accessToken = get_corp_weixin_token()
        if not accessToken:
            return HttpResponse(json.dumps({"errmsg":"miss token","errcode":1}))

        leaderidset = set()
        users = UserProfile.objects.all()
        for user in users:
            if user.isleader:
                leaderidset.add(user.corpweixinid)

        for department_id in ['1']:
            requrl = "https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token=%s&department_id=%s&fetch_child=1" % (accessToken,department_id)
            log.info("get userlist from %s" % requrl)

            rsp = requests.get(url=requrl)
            if rsp.status_code == 200:
                tmp_user_list = tmp_user_list + rsp.json()['userlist']

        for tmp_user in tmp_user_list:
            if tmp_user['enable'] == 1:
                isleader = False
                if tmp_user['userid'] in leaderidset:
                    isleader = True

                user_list.append({"userid":tmp_user['userid'],"name":tmp_user['name'], "department":tmp_user['department'], "avatar":tmp_user['avatar'], "isleader":isleader})

    return HttpResponse(json.dumps({"userlist":user_list,"errmsg":"","errcode":0}))

department_list_cache = []
last_cache_department_list_time = datetime.datetime.now()
def department_list(request):
    global department_list_cache, last_cache_department_list_time
    if request.method != "GET":
        return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

    if (datetime.datetime.now() - last_cache_department_list_time).days >= 1:
        last_cache_department_list_time = datetime.datetime.now()
        department_list_cache = []

    if not department_list_cache:
        accessToken = get_corp_weixin_token()
        if not accessToken:
            return HttpResponse(json.dumps({"errmsg":"miss token","errcode":1}))

        requrl = "https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=%s" % accessToken
        log.info("get departmentlist from %s" % requrl)

        rsp = requests.get(url=requrl)
        if rsp.status_code == 200:
            department_list_cache = department_list_cache + rsp.json()['department']

    return HttpResponse(json.dumps({"department":department_list_cache,"errmsg":"","errcode":0}))

# assessors data struct [[id,name],[id,name],[id,name]]
def beevaluation(request):
    if request.method == "GET":
        beevaluations = []
        quarter = get_quarter_name(datetime.datetime.now())
        bes = BeEvaluation.objects.filter(corpweixinid=request.user_id).order_by('-id')
        for be in bes:
            # 判断状态，如果所有人都对我进行了考评，则把状态修改成3
            if (quarter == be.quarter) and (be.state == 2):
                assessorset = set()
                jassessors = json.loads(be.assessors)
                for jassessor in jassessors:
                    assessorset.add(jassessor[0])

                finish = True
                es = Evaluation.objects.filter(corpweixinid=request.user_id)
                for e in es:
                    if e.assessorid not in assessorset:
                        finish = False
                        break

                if finish:
                    be.state = 3
                    be.save()

            beevaluations.append({"quarter":be.quarter, "corpweixinid":request.user_id, "assessors":be.assessors, "state":be.state, "createtime":str(be.createtime)})

        return HttpResponse(json.dumps({"beevaluation":beevaluations,"errmsg":"","errcode":0}))

    # 创建
    if request.method == "POST":
        quarter = get_quarter_name(datetime.datetime.now())
        bes = BeEvaluation.objects.filter(corpweixinid=request.user_id, quarter=quarter)

        # 需要判断当前季度是否已经创建
        if bes:
            return HttpResponse(json.dumps({"errmsg":u"已经创建过了，请不要重复创建","errcode":1}))

        PostData = json.loads(request.body)
        assessors = PostData['assessors']
        log.info("create assessors for:%s quarter: %s assessors: %s" % (request.user_id, quarter, assessors))

        users = UserProfile.objects.filter(corpweixinid=request.user_id)
        if not users:
            log.error("Wrong corp corpweixinid: %s" % request.user_id)
            return HttpResponse(json.dumps({"errmsg":"wrong corpweixinid","errcode":1}))

        jassessors = add_superiorid_into_assessors(assessors, users[0].superiorid, users[0].superiorname, request.user_id)
        if not jassessors:
            return HttpResponse(json.dumps({"errmsg":"assessors格式错误，请联系ghw","errcode":1}))

        if len(jassessors) > 12:
            return HttpResponse(json.dumps({"errmsg":u"邀请的人数过多，最多12个","errcode":1}))

        if len(jassessors) < 10:
            return HttpResponse(json.dumps({"errmsg":u"邀请的人数过少，最少10个","errcode":1}))

        BeEvaluation.objects.get_or_create(quarter=quarter, corpweixinid=request.user_id, name=users[0].username, superiorid=users[0].superiorid, assessors=json.dumps(jassessors), state=0)
        return HttpResponse(json.dumps({"errmsg":"","errcode":0}))

    # 修改
    if request.method == "PUT":
        PutData = json.loads(request.body)
        assessors = PutData['assessors']

        bes = None
        corpweixinid = None # 被评估的人的微信id
        quarter = get_quarter_name(datetime.datetime.now())
        if 'subordinateid' in PutData:
            corpweixinid = PutData['subordinateid']
            bes = BeEvaluation.objects.filter(corpweixinid=corpweixinid, superiorid=request.user_id, quarter=quarter)
            log.info("update assessors by leader %s for: %s quarter: %s assessors: %s" % (request.user_id, corpweixinid, quarter, assessors))
        else:
            corpweixinid = request.user_id
            bes = BeEvaluation.objects.filter(corpweixinid=corpweixinid, quarter=quarter)
            log.info("update assessors byself for: %s quarter: %s assessors: %s" % (request.user_id, quarter, assessors))

        if not bes:
            return HttpResponse(json.dumps({"errmsg":u"还没有创建评审，请先创建","errcode":1}))

        if bes[0].state != 0 and bes[0].state != 1:
            return HttpResponse(json.dumps({"errmsg":u"只有新建和待审核状态时才可以更新","errcode":1}))

        superiorname = ""
        try:
            users = UserProfile.objects.filter(corpweixinid=bes[0].superiorid)
            if users:
                superiorname = users[0].username
        except Exception as e:
            log.error("Exception: %s" % e)

        jassessors = add_superiorid_into_assessors(assessors, bes[0].superiorid, superiorname, corpweixinid)
        if not jassessors:
            return HttpResponse(json.dumps({"errmsg":"assessors格式错误，请联系ghw","errcode":1}))

        if len(jassessors) > 12:
            return HttpResponse(json.dumps({"errmsg":u"邀请的人数过多，最多12个","errcode":1}))

        if len(jassessors) < 10:
            return HttpResponse(json.dumps({"errmsg":u"邀请的人数过少，最少10个","errcode":1}))

        BeEvaluation.objects.filter(quarter=quarter, corpweixinid=corpweixinid).update(assessors=json.dumps(jassessors))
        return HttpResponse(json.dumps({"errmsg":"","errcode":0}))

    return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

def beevaluation_state(request):
    if request.method == "PUT":
        # 需要判断现在的状态-只有“新建 待审核”才能更改；需要把直属领导是否在里面；
        quarter = get_quarter_name(datetime.datetime.now())
        PutData = json.loads(request.body)
        action = PutData['action']# 1 为送审 2 为同意
        if action == 1:
            bes = BeEvaluation.objects.filter(corpweixinid=request.user_id, quarter=quarter)
            if not bes:
                return HttpResponse(json.dumps({"errmsg":u"请先创建考核","errcode":1}))

            be = bes[0]
            if be.state != 0:
                return HttpResponse(json.dumps({"errmsg":u"‘新建’状态只能‘送审’行为","errcode":1}))
            else:
                bes.update(state=1)
                send_corpweixin_msg(be.superiorid, u"请审核%s的邀请列表" % be.name)
                return HttpResponse(json.dumps({"errmsg":"","errcode":0}))
        elif action == 2:
            corpweixinid = PutData['beevaluationuserid']
            if not corpweixinid:
                return HttpResponse(json.dumps({"errmsg":u"同意行为时的参数错误","errcode":1}))

            bes = BeEvaluation.objects.filter(corpweixinid=corpweixinid, quarter=quarter)
            if not bes:
                return HttpResponse(json.dumps({"errmsg":u"请被考核人先创建考核","errcode":1}))

            be = bes[0]
            if be.superiorid != request.user_id:
                return HttpResponse(json.dumps({"errmsg":u"只有对方leader才能进行审核","errcode":1}))

            if be.state != 1:
                return HttpResponse(json.dumps({"errmsg":u"‘待审核’状态只能有‘同意’行为","errcode":1}))
            else:
                bes.update(state=2)

                # 插入评估表
                assessoridlist = []
                assessors = json.loads(be.assessors)
                for assessor in assessors:
                    Evaluation.objects.get_or_create(quarter=quarter, corpweixinid=corpweixinid, name=be.name, assessorid=assessor[0])
                    assessoridlist.append(assessor[0])

                send_corpweixin_msg([corpweixinid], u"你的邀请列表审核通过，请等待打分人员为你打分")
                send_corpweixin_msg(assessoridlist, u"%s邀请你为他／她的考核打分, 请登录<a href=\"http://evaluation.in.codoon.com\">考核系统</a>为他／她的考核打分" % be.name)
                return HttpResponse(json.dumps({"errmsg":"","errcode":0}))
        else:
            return HttpResponse(json.dumps({"errmsg":"wrong action","errcode":1}))
    else:
        return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

def checkevaluationlist(request):
    if request.method == "GET":
        beevaluations = []
        bes = BeEvaluation.objects.filter(superiorid=request.user_id)
        for be in bes:
            beevaluations.append({"quarter":be.quarter, "corpweixinid":be.corpweixinid, "name":be.name, "assessors":be.assessors, "state":be.state, "createtime":str(be.createtime)})

        return HttpResponse(json.dumps({"beevaluation":beevaluations,"errmsg":"","errcode":0}))

    return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

def evaluation(request):
    # 获取评估列表
    if request.method == "GET":
        evaluationlist = []
        objects = Evaluation.objects.filter(assessorid=request.user_id).order_by('-id')
        for one in objects:
            finish = not one.scorekeepin
            evaluationlist.append({"quarter":one.quarter,"beevaluationuserid":one.corpweixinid,"beevaluationusername":one.name,"state":2,"finish":finish,"detail":one.detail,"createtime":str(one.createtime)})
        
        return HttpResponse(json.dumps({"evaluation":evaluationlist,"errmsg":"","errcode":0}))

    # 考核和修改
    if request.method == "POST":
        PostData = json.loads(request.body)
        detail = PostData['detail']
        rawscore = PostData['rawscore']
        be_evaluation_userid = PostData['beevaluationuserid']

        quarter = get_quarter_name(datetime.datetime.now())
        bes = Evaluation.objects.filter(quarter=quarter, corpweixinid=be_evaluation_userid, assessorid=request.user_id, scorekeepin=True)
        if not bes:
            return HttpResponse(json.dumps({"errmsg":"不应该给此人打分","errcode":1}))

        if not bes[0].scorekeepin:
            return HttpResponse(json.dumps({"errmsg":"考核已完成，不能再修改分数","errcode":1}))

        bes.update(rawsocre=rawscore, detail=detail)
        return HttpResponse(json.dumps({"errmsg":"","errcode":0}))

    return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

def evaluation_state(request):
    # 考核完成
    if request.method == "PUT":
        PutData = json.loads(request.body)

        be_evaluation_userid = PutData['beevaluationuserid']
        quarter = get_quarter_name(datetime.datetime.now())
        bes = Evaluation.objects.filter(quarter=quarter, corpweixinid=be_evaluation_userid, assessorid=request.user_id)
        if not bes:
            return HttpResponse(json.dumps({"errmsg":"不应该考核此人","errcode":1}))

        bes.update(scorekeepin=False)
        return HttpResponse(json.dumps({"errmsg":"","errcode":0}))
    else:
        return HttpResponse(json.dumps({"errmsg":"wrong http method","errcode":1}))

def bakevaluation(request):
    quarter = get_quarter_name(datetime.datetime.now())
    EvaluationBak.objects.filter(quarter=quarter).delete()

    rets = Evaluation.objects.filter(quarter=quarter)
    for ret in rets:
        EvaluationBak.objects.create(quarter=ret.quarter, corpweixinid=ret.corpweixinid, name=ret.name, assessorid=ret.assessorid)

def calcscore(request):
    # 检查评估是否完成
    rets = Evaluation.objects.filter(scorekeepin=True)[:1]
    if rets:
        return HttpResponse(json.dumps({"errmsg":"还有部分人没有完成评估","errcode":1}))

    quarter = get_quarter_name(datetime.datetime.now())
    QuarterScore.objects.filter(quarter=quarter).delete()

    # 加载用户资料
    userinfomap = {}
    users = UserProfile.objects.all()
    for user in users:
        if user.enable:
            userinfomap[user.corpweixinid] = {'name':user.username, 'superiorid':user.superiorid, 'isleader':user.isleader, 'scoreproportion':user.scoreproportion}

    # 加载打分
    rawscore_by_assessor = {} # 一个人给非直属下属的打分map
    rawscore_by_leader = {} # 一个人给直属下属的打分map
    rets = Evaluation.objects.all()
    for ret in rets:
        if userinfomap[ret.corpweixinid]['superiorid'] == ret.assessorid: # 直属leader给自己的打分
            # ret.assessorid 是 ret.corpweixinid的直属领导
            if ret.assessorid in rawscore_by_leader:
                rawscore_by_leader[ret.assessorid].append([ret.rawsocre, ret.corpweixinid])
            else:
                rawscore_by_leader[ret.assessorid] = [ret.rawsocre, ret.corpweixinid]
        else:
            if ret.assessorid in rawscore_by_assessor:
                rawscore_by_assessor[ret.assessorid].append([ret.rawsocre, ret.corpweixinid])
            else:
                rawscore_by_assessor[ret.assessorid] = [[ret.rawsocre, ret.corpweixinid]]

    print "rawscore_by_assessor: ", rawscore_by_assessor
    print "rawscore_by_leader: ", rawscore_by_leader

    # 计算
    from calc_score import calc_score_imp
    ret_score_list, finalscoremap = calc_score_imp(userinfomap, rawscore_by_assessor, rawscore_by_leader)
    print "ret_score_list:", ret_score_list
    print "finalscoremap:", finalscoremap

    # ret_score_list [[corpweixinid, assessorid, socre],[corpweixinid, assessorid, socre]]
    for ret_score_str in ret_score_list:
        corpweixinid = ret_score_str[0]
        assessorid = ret_score_str[1]
        socre = ret_score_str[2]
        Evaluation.objects.filter(quarter=quarter, corpweixinid=corpweixinid, assessorid=assessorid).update(socre=socre)

    #{uid:finalscore}
    for corpweixinid in finalscoremap:
        qs = QuarterScore(quarter=quarter, corpweixinid=corpweixinid, name=userinfomap[corpweixinid]['name'], socre=finalscoremap[corpweixinid])
        qs.save()

    return HttpResponse(json.dumps({"errmsg":"Succ","errcode":0}))
