import numpy as np
import pickle
from collections import defaultdict

import pdb
def output(Q_val, I_val, QI_val, C_val, printAnswer, iterator):
    
    
    # given the image, question, and caption, store the corresponding label for each    
    count = 0
    data = defaultdict(list)
    for imageId, question, answer, caption in iterator:
        uData = {}
        uData['question'] = question
        uData['answer'] = answer
        uData['caption'] = caption
        uData['Q_ans'] = printAnswer[Q_val[count]]
        uData['I_ans'] = printAnswer[I_val[count]]
        uData['QI_ans'] = printAnswer[QI_val[count]]
        uData['C_ans'] = printAnswer[C_val[count]]
        data[imageId].append(uData)
        count += 1


    pair = []
    for key, value in data.iteritems():
        pair.append({'imgId':key, 'text':value})
    return pair




def uniqueVec(data, k):
    # return the top k unique vector of the matrix.
    a = np.array(data)
    b = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
    _, idx = np.unique(b, return_index=True)
    _, count = np.unique(b, return_counts=True)

    # return top k. 
    ind = np.argsort(-count)
    return a[idx[ind[:k]]], count[ind[:k]], idx[ind[:k]]

def filterVec(vecs, answerVec, questionVec):

    TrainLabel = []
    TrainVec = []
    AnswerVec = []
    counts = 0
    for i in answerVec:
        tmp = 0
        for vec in vecs:
            if (vec==i).all():
                label = tmp
                TrainLabel.append(label)
                TrainVec.append(questionVec[counts])
                AnswerVec.append(vec)
            tmp += 1
        counts += 1
    return TrainLabel, TrainVec, AnswerVec

def fallKplus1(y_val, k):
    count = 0
    right = 0
    for i in y_val:
        
        if i == k:
            right += 1
        count += 1
    accuracy = np.float(right) / count
    print ' %.4f' %(accuracy),

def calAccuracy(y_val, W2VAnswerNear, W2VAnswerTest, answerGroup):
    right = 0
    for group in answerGroup:
        group_right = 0
        for Testid in group:
            flag = 0
            for GTid in group:
                if (W2VAnswerNear[y_val[GTid]] == W2VAnswerTest[Testid]).all():
                    flag = 1
            group_right += flag
        right += group_right

    accuracy = np.float(right) / len(y_val)
    print ' %.4f' %(accuracy),

def labelAccuracy(y_val, label):
    count = 0
    right = 0
    for i in range(len(y_val)):
        count += 1
        if y_val[i] == label[i]:
            right += 1

    accuracy = np.float(right) / count
    print '%.4f' %(accuracy),

def mlpOPlable(out, gt, answerGroup, numAnswer):
    label_count = np.zeros(numAnswer)
    soft_right = 0
    for group in answerGroup:
        # assign soft error. 
        flag = 0
        label = out[group[0]]
        label_count[label] += 1
        for GTid in group:
            if gt[GTid] == label:
                flag += 1

        soft_right += flag / len(group)

    accuracy = np.float(soft_right) / len(answerGroup)
    print 'The Open-answer task Acc is %.4f' %(accuracy)
    return label_count

def mlpOPAcc(out, gt, answerGroup, numAnswer):
    label_count = np.zeros(numAnswer)
    soft_right = 0
    for group in answerGroup:
        # assign soft error. 
        flag = 0
        label = out[group[0]].index(max(out[group[0]]))
        label_count[label] += 1
        for GTid in group:
            if gt[GTid] == label and label != numAnswer:
                flag += 1
        
        soft_right += (flag / len(group))

    accuracy = np.float(soft_right) / len(answerGroup)
    print 'The Open-answer task with %d Question, Acc is %.4f' %(len(answerGroup),accuracy)
    return label_count


def mlpOPAccfilter(out, gt, answerGroup, multiAnswer, numAnswer):
    label_count = np.zeros(numAnswer)
    soft_right = 0
    count = 0
    for group in answerGroup:
        # assign soft error. 
        choice = multiAnswer[group[0]]
        if len(choice) > 0:    
            flag = 0
            label = out[group[0]].index(max(out[group[0]]))
            label_count[label] += 1
            for GTid in group:
                if gt[GTid] == label and label != numAnswer:
                    flag += 1
            
                if sum(np.array(choice)==gt[GTid]) != 1 and gt[GTid] != numAnswer:
                    print 'error' 

            soft_right += flag / len(group)
            count += 1
    accuracy = np.float(soft_right) / count
    print 'The Open-answer task with %d Question, Acc is %.4f' %(count,accuracy)
    return label_count


def mlpMSAcc(out, gt, answerGroup, multiAnswer, numAnswer):
    count = 0
    soft_right = 0
    for group in answerGroup:
        choice = multiAnswer[group[0]]
        if len(choice) > 0:
            selectScore = []
            for idx in choice:
                if idx != numAnswer:
                    selectScore.append(out[group[0]][idx])
                else:
                    selectScore.append(0)
            label = choice[selectScore.index(max(selectScore))]
            flag = 0
            for GTid in group:
                if gt[GTid] == label:
                    flag += 1

            soft_right += (flag / len(group))
            count += 1
    accuracy = np.float(soft_right) / count
    print 'The Multi choice task with %d Question, Acc is %.4f' %(count, accuracy)

def printAnswer(ixtoword, vecs, counts):
    store = []
    for i in range(len(vecs)):
        string = ''
        for j in range(len(vecs[i])):
            if vecs[i][j] > 0:
                string = string + ' ' + ixtoword.get(j, 'NoInVocab')
        #print '%s %d' %(string, counts[i]),
        store.append(string)
    #print ''
    return store

def intersction(x,y):
    # intersction kernel
    return np.minimum(x,y).sum()


def pickleLoad(path):
    
    f = open(path)
    data = pickle.load(f)
    f.close()

    return data

def pickleSave(path, data):
    f = open(path, 'w')
    pickle.dump(data, f)
    f.close()