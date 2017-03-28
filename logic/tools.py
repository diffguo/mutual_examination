#coding=utf-8
import json
import datetime

def get_quarter_name(time):
    if time.month in [1,2,3]:
        return str(time.year-1) + u"年Q4"
    
    if time.month in [4,5,6]:
        return str(time.year) + u"年Q1"
    
    if time.month in [7,8,9]:
        return str(time.year) + u"年Q2"

    if time.month in [10,11,12]:
        return str(time.year) + u"年Q3"

def add_superiorid_into_assessors(assessors, superiorid, superiorname, selfcorpweixinid):
    jassessors = []
    have_superiorid = False
    for assessor in assessors:
        if isinstance(assessor, list) and len(assessor) == 2:
            if assessor[0] == superiorid:
                have_superiorid = True

            if assessor[0] != selfcorpweixinid:
                jassessors.append(assessor)
        else:
            return []

    if not have_superiorid:
        jassessors.append([superiorid, superiorname])

    return jassessors

if __name__ == '__main__':
    print get_quarter_name(datetime.datetime(2016,10,1))
    print get_quarter_name(datetime.datetime(2016,11,26))
    print get_quarter_name(datetime.datetime(2016,12,15))
    print get_quarter_name(datetime.datetime(2017,1,1))
    print get_quarter_name(datetime.datetime(2017,2,26))
    print get_quarter_name(datetime.datetime(2017,3,15))
    print get_quarter_name(datetime.datetime(2017,4,1))
    print get_quarter_name(datetime.datetime(2017,5,26))
    print get_quarter_name(datetime.datetime(2017,6,15))
    print get_quarter_name(datetime.datetime(2017,7,1))
    print get_quarter_name(datetime.datetime(2017,8,26))
    print get_quarter_name(datetime.datetime(2017,9,15))
    print get_quarter_name(datetime.datetime(2017,10,1))
    print get_quarter_name(datetime.datetime(2017,11,26))
    print get_quarter_name(datetime.datetime(2017,12,15))