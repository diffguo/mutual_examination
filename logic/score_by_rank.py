#coding=utf-8

import types
import numpy as np

def BinarySearchByLog(score_list, step_len, level, stc_fc, fc_diff_limit):
    #print "Start binarySearchByLogFunc  score_list: ", score_list, step_len, level, stc_fc, fc_diff_limit

    step = 20
    for i in range(step):
        tmp_step_len = step_len - i*10.0/pow(10, level)
        start = 60 + (40 - (len(score_list) - 1)*tmp_step_len)/2
        #print "tmp_step_len: ", tmp_step_len, start
        tmp_score_list = [start + index*tmp_step_len for index in range(len(score_list))]
        #print "tmp_score_list: ", tmp_score_list, np.std(tmp_score_list)
        fc = np.std(tmp_score_list)
        if fc > stc_fc:
            if fc - stc_fc <= fc_diff_limit:
                return (tmp_step_len, tmp_score_list)
        elif fc < stc_fc:
            tmp_step_len = step_len - (i-1)*10.0/pow(10, level)
            start = 60 + (40 - (len(score_list) - 1)*tmp_step_len)/2
            tmp_score_list = [start + index*tmp_step_len for index in range(len(score_list))]
            return BinarySearchByLog(tmp_score_list, tmp_step_len, level+1, stc_fc, fc_diff_limit)
        else:
            return (tmp_step_len, tmp_score_list)

    print "Fatal Error!!! "
    return []

def InnerGenStdScoreList(obj_num):
    if obj_num == 1:
        step_len = 0
        score_list = [80]
    else:
        score_list = []
        step_len = (100.0 - 60.0) / (obj_num-1)

        for j in range(obj_num):
            score_list.append(60 + step_len*j)

        step_len, score_list = BinarySearchByLog(score_list, step_len, 1, 11.8, 0.01)

        score_list = [round(score,3) for score in score_list]

    #print "std score list: ",score_list,sum(score_list)/len(score_list),np.std(score_list)
    return (step_len, score_list)

def GenAllStdScoreList():
    for obj_num in range(50):
        print "obj_num: ",obj_num+1
        InnerGenStdScoreList(obj_num+1)

# rank_list type: [[1,1,1],[1,1],[1,1,1],1,1]
def GenScoreListByRankV1(rank_list):
    obj_num = 0
    for i in range(len(rank_list)):
        if type(rank_list[i]) == types.ListType:
            obj_num += len(rank_list[i])
        else:
            obj_num += 1

    step_len, std_score_list = InnerGenStdScoreList(obj_num)

    score_list = []
    # now_score 为当前的起始分数，每次加上步长
    now_score = 60 + (40 - (len(std_score_list) - 1)*step_len)/2
    for i in range(len(rank_list)):
        if type(rank_list[i]) == types.ListType:
            now_len = len(rank_list[i])
            for j in range(len(rank_list[i])):
                score_list.append(now_score + step_len*(now_len-1)/2)
            now_score += step_len*len(rank_list[i])
        else:
            score_list.append(now_score)
            now_score += step_len

    score_list = [round(score,3) for score in score_list]
    return score_list
    #print "result score list: ",score_list,sum(score_list)/len(score_list),np.std(score_list)

# rank_list type: [[[1,uid],[1,uid],[1,uid]],[[1,uid],[1,uid]],[1,uid]]. 即排名携带用户信息
def GenScoreListByRankV2(rank_list):
    obj_num = 0
    for i in range(len(rank_list)):
        if type(rank_list[i][0]) == types.ListType:
            obj_num += len(rank_list[i])
        else:
            obj_num += 1

    step_len, std_score_list = InnerGenStdScoreList(obj_num)

    score_list = []
    # now_score 为当前的起始分数，每次加上步长
    now_score = 60 + (40 - (len(std_score_list) - 1)*step_len)/2
    for i in range(len(rank_list)):
        if type(rank_list[i][0]) == types.ListType:
            now_len = len(rank_list[i])
            for j in range(len(rank_list[i])):
                score_list.append([now_score + step_len*(now_len-1)/2, rank_list[i][j][1]])
            now_score += step_len*len(rank_list[i])
        else:
            score_list.append([now_score, rank_list[i][1]])
            now_score += step_len

    score_list = [[round(score[0],3), score[1]] for score in score_list]
    return score_list
    #print "result score list: ",score_list,sum(score_list)/len(score_list),np.std(score_list)

#RawScoreList: [[rawscore, userid],[rawscore, userid],[rawscore, userid],[rawscore, userid]]
def CalcScoreListByRawScoreList(RawScoreList):
    if len(RawScoreList) <= 2:
        return []
    
    cell = []
    aggregate_list = []
    RawScoreList.sort()
    for i in range(len(RawScoreList)):
        if cell:
            if cell[-1][0] == RawScoreList[i][0]:
                cell.append(RawScoreList[i])
            else:
                if len(cell) == 1:
                    aggregate_list.append(cell[0])
                else:
                    aggregate_list.append(cell)

                cell = [RawScoreList[i]]
        else:
            cell.append(RawScoreList[i])

    if cell:
        if len(cell) == 1:
            aggregate_list.append(cell[0])
        else:
            aggregate_list.append(cell)

    score_list = GenScoreListByRankV2(aggregate_list)
    print "aggregate_list: ", aggregate_list
    print "score_list: ", score_list

    return score_list

if __name__ == '__main__':
    GenAllStdScoreList()

    # rank_list = [[7,6,5,6,6],[2,2,2,4,4]]
    # GenScoreListByRank(rank_list)

    # rank_list = [[7,6,5],[6,6,2,2],[2,4,4]]
    # GenScoreListByRank(rank_list)

    # rank_list = [[1,6,7],[4,5,8],3,2]
    # GenScoreListByRank(rank_list)

    # rank_list = [1,[7,5,8],[6,3],2,4]
    # GenScoreListByRank(rank_list)

    # rank_list = [1,7,5,[6,3],[8,4],2]
    # GenScoreListByRank(rank_list)

    # rank_list = [[7,3],[5,6,8],[1,4],2]
    # GenScoreListByRank(rank_list)

    # rank_list = [[7,5,8,1],[3,4],6,2]
    # GenScoreListByRank(rank_list)
    
    # raw_score_list_1 = [[7,5],[5,2],[2,6],[2,4],[7,4]]
    # CalcScoreListByRawScoreList(raw_score_list_1)
