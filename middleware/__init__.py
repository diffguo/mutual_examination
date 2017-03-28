# -*- coding: utf-8 -*-
import time
import json
from mutual_examination.settings import log
from django.http import HttpResponseRedirect,HttpResponse
from django.utils.crypto import constant_time_compare
from logic.login import LoginUrl, SESSION_USER_ID_KEY, SESSION_USER_HASH_KEY, get_session_auth_hash

def check_session(request):
    if not SESSION_USER_ID_KEY in request.session:
        return False

    if not SESSION_USER_HASH_KEY in request.session:
        return False

    request.user_id = request.session[SESSION_USER_ID_KEY]
    session_hash = request.session[SESSION_USER_HASH_KEY]
    session_hash_verified = session_hash and constant_time_compare(
        session_hash,
        get_session_auth_hash(request, request.session[SESSION_USER_ID_KEY])
    )

    if not session_hash_verified:
        request.session.flush()
        return False

    return True

# user and auth
class UserMiddleware(object):

    def process_request(self, request):

        assert hasattr(request, 'session'), (
            "The UserMiddleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE%s setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'UserMiddleware'."
        ) % ("_CLASSES" if settings.MIDDLEWARE is None else "")

        if request.path.startswith('/api/islogin'):
            ok = check_session(request)
            if ok :
                return HttpResponse(json.dumps({"errmsg":"","errcode":0}))
            else:
                return HttpResponse(json.dumps({"errmsg":"needlogin","errcode":9999,"url":LoginUrl}))

        if not request.path.startswith('/api/login'):
            ok = check_session(request)
            if ok:
                setattr(request, "_process_start_timestamp", time.time())
            else:
                return HttpResponse(json.dumps({"errmsg":"needlogin","errcode":9999,"url":LoginUrl}))

    def process_response(self, request, response):
        try:
            if hasattr(request, '_process_start_timestamp'):
                used_time = int((time.time() - float(getattr(request, '_process_start_timestamp'))))
                if used_time >= 3:
                    user_id = 'anymouse'
                    if hasattr(request, 'user'):
                        user_id = request.user.corpweixinid
                    log.ERROR("LONG_PROCESS: %s %s %s" % (user_id, used_time, request.get_full_path()[:200]))
        except Exception, e:
            log.ERROR("process_response error: %s" % str(e))

        return response
        
        