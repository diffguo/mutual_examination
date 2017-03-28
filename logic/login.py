#coding=utf-8
import requests
from mutual_examination.settings import log
from corpwx_api_tools import get_corp_weixin_token, CorpID, AgentId
from models import UserProfile
from django.utils.crypto import salted_hmac
from django.http import HttpResponseRedirect, HttpResponse

SESSION_USER_ID_KEY = '_eriowUht2er'

SESSION_USER_HASH_KEY = '_ywetblkItgy'

LoginUrl = "https://open.work.weixin.qq.com/wwopen/sso/qrConnect?appid=%s&agentid=%s&redirect_uri=https://login-in.codoon.com/weixin/redirect&state=http://evaluation.in.codoon.com/api/login/" % (CorpID, AgentId)

# demo {"UserId":"14006","DeviceId":"","errcode":0,"errmsg":"ok"}
def get_corp_weixin_user_id(code):
    accessToken = get_corp_weixin_token()
    if not accessToken:
        return None

    requrl = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo?access_token=%s&code=%s" % (accessToken, code)
    log.info("get_corp_weixin_user_id url: %s" % requrl)
    rsp = requests.get(url=requrl)

    if rsp.status_code == 200:
        jrsp = rsp.json()
        if 'UserId' in jrsp:
            corpweixinid = jrsp['UserId']

            # 用户数据是初始化的，不再生成
            # try:
            #     users = UserProfile.objects.filter(corpweixinid=corpweixinid)
            #     if not users:
            #         requrl_user = "https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token=%s&userid=%s" % (accessToken, corpweixinid)
            #         rsp_user = requests.get(url=requrl_user)
            #         if rsp_user.status_code == 200:
            #             jrsp_user = rsp_user.json()
            #             if 'errcode' in jrsp_user and jrsp_user['errcode'] == 0:
            #                 new_user = UserProfile(corpweixinid=corpweixinid, username=jrsp_user['name'], department=jrsp_user['department'],position=jrsp_user['position'],mobile=jrsp_user['mobile'],email=jrsp_user['email'],gender=jrsp_user['gender'],avatar=jrsp_user['avatar'],enable=(jrsp_user['enable'] == 1))
            #                 new_user.save()
            #                 log.info("New User: %s" % rsp_user.text)
            #             else:
            #                 log.error("Get User (%s) Detail Info from qywx error: %s" % (corpweixinid, rsp_user.text))
            #         else:
            #             log.error("Get User (%s) Detail Info from qywx fail: %s" % (corpweixinid, rsp_user.text))
            # except Exception as e:
            #     log.error("Save QyWx UserInfo Fail: %s" % e)

            return corpweixinid
        else:
            log.error("get_corp_weixin_user_id from qyapi.weixin.qq.com error. rsp text: %s" % rsp.text)
    else:
        log.error("get_corp_weixin_user_id from qyapi.weixin.qq.com fail. status_code: %s" % rsp.status_code)

    return None

def get_user_ip(request):
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):  
        ip =  request.META['HTTP_X_FORWARDED_FOR']  
    else:  
        ip = request.META['REMOTE_ADDR']  

def get_session_auth_hash(request, user_id):
        key_salt = "logic.models.get_session_auth_hash.ffer435U7B"
        return salted_hmac(key_salt, "%s_authhash_%s" % (get_user_ip(request), user_id)).hexdigest()

def session_login(request, corpweixinid):
    session_hash = get_session_auth_hash(request, corpweixinid)

    # if SESSION_USER_ID_KEY in request.session:
    #     request.session.flush()
    # else:
    #     request.session.cycle_key()
    # write into db???
    request.session.flush()

    request.session[SESSION_USER_ID_KEY] = corpweixinid
    request.session[SESSION_USER_HASH_KEY] = session_hash

def login(request):
    code = request.GET.get('code')
    if not code:
        log.error("Wrong Login Para: %s" % request.GET)
        return HttpResponseRedirect(LoginUrl)

    corpweixinid = get_corp_weixin_user_id(code)
    if not corpweixinid:
        log.error("get_corp_weixin_user_id error")
        return HttpResponse(u"获取信息失败，请联系管理员")
    else:
        # login succ
        users = UserProfile.objects.filter(corpweixinid=corpweixinid)
        if users:
            session_login(request, corpweixinid)
        else:
            log.error("Login Fail For Read User From Table UserProfile error, corpweixinid: %s" % corpweixinid)
            return HttpResponse(u"非考评系统成员，不能登陆，sorry！")

    return HttpResponseRedirect("http://evaluation.in.codoon.com/#!/home")

def logout(request):
    request.session.flush()
    return HttpResponse('bye')

def init(request):
    # 同步人员
    accessToken = get_corp_weixin_token()
    if not accessToken:
        return HttpResponse(json.dumps({"errmsg":"miss token","errcode":1}))

    corpweixinidset = set()
    for department_id in ['10000815', '10005623']:
        requrl = "https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token=%s&department_id=%s&fetch_child=1" % (accessToken,department_id)
        rsp = requests.get(url=requrl)

        userlist = rsp.json()['userlist']

        alluser = UserProfile.objects.all()
        for user in alluser:
            corpweixinidset.add(user.corpweixinid)

        for jrsp_user in userlist:
            if jrsp_user['userid'] not in corpweixinidset:
                corpweixinidset.add(jrsp_user['userid'])
                new_user = UserProfile(corpweixinid=jrsp_user['userid'], username=jrsp_user['name'], department=jrsp_user['department'],position=jrsp_user['position'],mobile=jrsp_user['mobile'],email=jrsp_user['email'],gender=jrsp_user['gender'],avatar=jrsp_user['avatar'],enable=(jrsp_user['enable'] == 1))
                new_user.save()

    # 初始化isleader
    for corpweixinid in corpweixinidset:
        users = UserProfile.objects.filter(superiorid=corpweixinid)
        if users:
            UserProfile.objects.filter(corpweixinid=corpweixinid).update(isleader=True)

    # 清理评估表, Todo：下个季度写
    # objects = Evaluation.objects.exclude(quarter=quartername)
    # for one in objects:
    #     bakeone = EvaluationBak()

    return HttpResponse(json.dumps({"errmsg":"succ","errcode":0}))
