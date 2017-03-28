#coding=utf-8

import numpy
from score_by_rank import CalcScoreListByRawScoreList

def calc_score_imp(userinfomap, rawscore_by_assessor, rawscore_by_leader):
    # 通过打分人计算出分数: 先通过rawscore得到排名，再通过排名得到分数, leader对别人的考核要分成两步：对其他人的考核，对直属下属的考核
    socre_by_leader = {}
    socre_by_assessors = {}
    ret_score_list = [] 

    # 计算一个人给非直属下属打分
    for assessorid in rawscore_by_assessor:
        score_list = CalcScoreListByRawScoreList(rawscore_by_assessor[assessorid])
        for score in score_list:
            if score[1] in socre_by_assessors:
                socre_by_assessors[score[1]].append(score[0])
            else:
                socre_by_assessors[score[1]] = [score[0]]

            ret_score_list.append([score[1], assessorid, score[0]])

    # 计算一个人给直属下属打分
    for leaderid in rawscore_by_leader:
        score_list = CalcScoreListByRawScoreList(rawscore_by_leader[leaderid])
        for score in score_list:
            socre_by_leader[score[1]] = [leaderid, score[0]]
            ret_score_list.append([score[1], leaderid, score[0]])

    # 计算最终分数，对考核人来说，最终分数为：为其打分的人的人的平均分(排除其直属领导的打分) * (1-直属领导的占比) + 直属领导的打分*直属领导的占比
    finalscoremap = {}
    for uid in socre_by_assessors:
        finalscore = float(numpy.sum(socre_by_assessors[uid]))/len(socre_by_assessors[uid])
        if uid in socre_by_leader:
            leaderid_and_score = socre_by_leader[uid]
            leaderid = leaderid_and_score[0]
            leaderscore = leaderid_and_score[1]
            leaderscoreproportion = userinfomap[leaderid]['scoreproportion']

            finalscore = (1-leaderscoreproportion)*finalscore + leaderscoreproportion*leaderscore
            finalscoremap[uid] = finalscore
        else:
            finalscoremap[uid] = finalscore

    # ret_score_list [[corpweixinid, assessorid, socre],[corpweixinid, assessorid, socre]]
    # finalscoremap {uid:finalscore}
    return (ret_score_list, finalscoremap)

if __name__ == '__main__':
    userinfomap = {}
    rawscore_by_leader = {}
    rawscore_by_assessor = {}

    userinfomap[1] = {'scoreproportion':0.5}
    rawscore_by_assessor[4] = [[85,2],[93,3],[77,1]]
    rawscore_by_assessor[5] = [[92,2],[66,3],[79,1],[83,4]]
    rawscore_by_leader[1] = [[80,2],[70,3],[90,4]]

    ret_score_list, finalscoremap = calc_score_imp(userinfomap, rawscore_by_assessor, rawscore_by_leader)
    print ret_score_list
    print finalscoremap

