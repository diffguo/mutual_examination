#coding=utf-8
import json
import requests
import datetime
from models import TCorpWeixinToken
from mutual_examination.settings import log

AgentId = "1000012"

CorpID = "WWeb430e32f7c079ce"

Secret = "XVXn3xKb549IUb8KBN9pgTeSoFgbxr6vo-Qww9wRc24"

CorpWeixinToken = ""

CorpWeixinTokenExpireDatetime = datetime.datetime.now()

def get_corp_weixin_token():
    global CorpWeixinToken, CorpWeixinTokenExpireDatetime
    if not CorpWeixinToken:
        objects = TCorpWeixinToken.objects.all()[:1]
        if objects:
            CorpWeixinToken = objects[0].accesstoken
            CorpWeixinTokenExpireDatetime = objects[0].expiresdatetime

    nowtime = datetime.datetime.now()
    if nowtime > CorpWeixinTokenExpireDatetime:
        requrl = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s" % (CorpID, Secret)
        log.info("get token url: %s" % requrl)
        rsp = requests.get(url=requrl)

        if rsp.status_code == 200:
            jrsp = rsp.json()
            if 'access_token' in jrsp:
                CorpWeixinToken = jrsp['access_token']
                CorpWeixinTokenExpireDatetime = nowtime + datetime.timedelta(seconds=jrsp['expires_in'])

                TCorpWeixinToken.objects.all().delete()
                TCorpWeixinToken(accesstoken=CorpWeixinToken, expiresdatetime=CorpWeixinTokenExpireDatetime).save()
            else:
                log.error("get_corp_weixin_token from qyapi.weixin.qq.com error. rsp text: %s" % rsp.text)
        else:
            log.error("get_corp_weixin_token from qyapi.weixin.qq.com error. status_code: %s" % rsp.status_code)

    return CorpWeixinToken

def get_department_list(department_id):
    accessToken = get_corp_weixin_token()
    if department_id:
        requrl = "https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=%s&id=%d" % (accessToken,department_id)
    else:
        requrl = "https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=%s" % accessToken

    rsp = requests.get(url=requrl)

    if rsp.status_code == 200:
        return rsp.json()['department']
    else:
        return None

def get_member_list(department_id):
    accessToken = get_corp_weixin_token()
    requrl = "https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token=%s&department_id=%s&fetch_child=1" % (accessToken,department_id)
    rsp = requests.get(url=requrl)

    if rsp.status_code == 200:
        return rsp.json()['userlist']
    else:
        return None

def send_corpweixin_msg(touseridlist, content):
    touseridstr = ""
    for i in range(len(touseridlist)):
        if i == 0:
            touseridstr = touseridlist[i]
        else:
            touseridstr += "|" + touseridlist[i]
            
    msgst = {
        "touser" : touseridstr,
        "msgtype" : "text",
        "agentid" : 1000012,
        "text" : {
                "content" : content
           }
    }

    headerst = {"Content-Type": "application/json; charset=utf-8"}
    requrl = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % get_corp_weixin_token()
    rsp = requests.post(url=requrl, headers=headerst, data=json.dumps(msgst))

    if rsp.status_code != 200:
        log.error("send msg to weixin status_code error: %s. data: %s" % (rsp.status_code, json.dumps(msgst)))
        return False

    if rsp.json()['errcode'] != 0:
        log.error("send msg to weixin ret error: %s. data: %s" % (rsp.text, json.dumps(msgst)))
        return False

    return True

if __name__ == '__main__':
    # 获取研发部门的成员列表
    # print get_member_list(10000815)

    # 获取所有部门名
    # for one in get_department_list(0):
    #     print one['order'], one['parentid'], one['name']

    # 获取产品团队的子团队列表
    # for one in get_department_list(10005623):
    #     print one['order'], one['parentid'], one['name']

    # 获取产品设计部门的成员列表
    # for one in get_member_list(10005623):
    #     print one['name'], one['department'], one['position']

    # 发送消息
    print send_corpweixin_msg(['14006'], "Test")
