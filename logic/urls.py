from django.conf.urls import url
import views,login

urlpatterns = [
    url(r'^api/init$',login.init),
    url(r'^api/login/?$',login.login),
    url(r'^api/logout/?$',login.logout),
    url(r'^api/calcscore/?$',views.calcscore),
    url(r'^api/bakevaluation/?$',views.bakevaluation),

    url(r'^api/userinfo/?$',views.userinfo),
    url(r'^api/department/list/?$',views.department_list),
    url(r'^api/department/user/list/?$',views.department_user_list),

    url(r'^api/beevaluation/?$',views.beevaluation),
    url(r'^api/beevaluation/state/?$',views.beevaluation_state),
    url(r'^api/checkevaluationlist/?$',views.checkevaluationlist),

    url(r'^api/evaluation/?$',views.evaluation),
    url(r'^api/evaluation/state/?$',views.evaluation_state),
]