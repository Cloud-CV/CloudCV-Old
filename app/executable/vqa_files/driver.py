# VQA MLP baseline for CloudCV
# author: Jiasen Lu, Devi Parikh

import json
import numpy as np
import os
import sys
import pdb
import time
import pickle
import utils
import operator

import scipy.io
from data_provider import getDataProvider
from tools import SVM
from tools import kmeans
from MLP import test_mlp
from collections import defaultdict
from random import randint

def preProBuildWordVocabAll(question_iterator, caption_iterator, word_count_threshold):
    # count all word counts and threshold
    print 'preprocessing word counts and creating vocab based on word count threshold %d' % (word_count_threshold, )
    t0 = time.time()

    word_counts = {}
    nsents = 0
    for sent in question_iterator:
        nsents += 1
        for w in sent:
            word_counts[w] = word_counts.get(w, 0) + 1

    nsents = 0
    for sent in caption_iterator:
        nsents += 1
        for w in sent:
            word_counts[w] = word_counts.get(w, 0) + 1

    vocab = [w for w in word_counts if word_counts[w] >= word_count_threshold]
    vocab.remove('')
    print 'filtered words from %d to %d in %.2fs' % (len(word_counts)-1, len(vocab), time.time() - t0)

    ixtoword = {}
    wordtoix = {}
    ix = 0
    for w in vocab:
        wordtoix[w] = ix
        ixtoword[ix] = w
        ix += 1
    return wordtoix, ixtoword, vocab

def preProBuildWordVocab(iterator, dic_size, word_order = 0):
    # word_order: the order of word in the sentece should be count, 0 means all the sentence.
    # dic_size: the size of dictionay to creat, if == 0. then will preserve all the words.
    # count all word counts and threshold
    print 'preprocessing word counts and creating vocab based on dictionary size %d' % (dic_size, )
    t0 = time.time()

    word_counts = {}
    nsents = 0

    for sent in iterator:
        nsents += 1
        if word_order == 0:
            for w in sent:
                word_counts[w] = word_counts.get(w, 0) + 1
        else:
            if len(sent) >= word_order:
                w = sent[word_order-1]
                word_counts[w] = word_counts.get(w, 0) + 1
    if dic_size == 0:
        vocab = sorted(word_counts, key=word_counts.get, reverse=True)
    else:
        vocab = sorted(word_counts, key=word_counts.get, reverse=True)[:dic_size]

    print 'filtered words from %d to %d in %.2fs' % (len(word_counts)-1, len(vocab), time.time() - t0)

    ixtoword = {}
    wordtoix = {}
    ix = 0
    for w in vocab:
        wordtoix[w] = ix
        ixtoword[ix] = w
        ix += 1
    return wordtoix, ixtoword, vocab


def preProBuildAnswerVocab(iterator, dic_size = 1000):
    print 'preprocessing answer counts and creating vocab based on dictionary size %d' % (dic_size, )
    t0 = time.time()
    answer_counts = {}
    nsents = 0

    for sent in iterator:
        nsents += 1
        sent_string = ' '.join(sent)
        # group the list to string. 
        answer_counts[sent_string] = answer_counts.get(sent_string, 0) + 1

    if dic_size == 0:
        vocab = sorted(answer_counts, key=answer_counts.get, reverse=True)
    else:
        vocab = sorted(answer_counts, key=answer_counts.get, reverse=True)[:dic_size]

    print 'filtered answers from %d to %d in %.2fs' % (len(answer_counts)-1, len(vocab), time.time() - t0)

    ixtoword = {}
    wordtoix = {}
    ix = 0
    for w in vocab:
        wordtoix[w] = ix
        ixtoword[ix] = w
        ix += 1
    return wordtoix, ixtoword, vocab

def preProBuildAnswerVocabTop(dp, th=25):
    t0 = time.time()

    # creat a queue with question and count, each time, find the questio with the most count and
    # +1 on question length, until all the question reach the threshold, or reach the question length.

    ques_len = 1

    # initialize with 2.

    answer_counts = {}
    nsents = 0
    # creat a vector corresponding to the depth of all the answers.
    ques_depth = []
    for sent in dp.iterQuestion('train'):
        nsents += 1
        sent_string = ' '.join(sent[:ques_len])
        # group the list to string. 
        ques_depth.append(ques_len)
        answer_counts[sent_string] = answer_counts.get(sent_string, 0) + 1

    # filter the answer which is larger than threshold.
    vocab = [w for w in answer_counts if answer_counts[w] >= th]

    # for each the answer_count which is larger than th, +1 on question length, until reach the threshold or reach the question lenghth.
    check_len = CheckVocabTop(dp.iterQuestion('train'), vocab, ques_depth)
    print 'filtered answers from %d to %d in %.2fs' % (len(answer_counts)-1, len(vocab), time.time() - t0)

    # while there exist question type which didn't exceed maximum question length and threshold.
    Flag = 0
    count = 0
    while(Flag == 0):
        answer_counts, ques_depth = AnswerVocabTop(dp.iterQuestion('train'), vocab, answer_counts, ques_depth, check_len, th)
        vocab = [w for w in answer_counts if answer_counts[w] >= th]
        check_len = CheckVocabTop(dp.iterQuestion('train'), vocab, ques_depth)

        # check if there still exist question can go further?
        Flag = 1
        for sent in vocab:
            if check_len[sent] == 0 and answer_counts[sent] >= th:
                Flag = 0


        count+=1
        print '%d' % count

    ques_depth = np.array(ques_depth) - 1
    ques_depth[ques_depth==0] = 1

    answer_counts = {}
    nsents = 0
    for sent in dp.iterQuestion('train'):
        sent_string = ' '.join(sent[:ques_depth[nsents]])
        answer_counts[sent_string] = answer_counts.get(sent_string, 0) + 1
        nsents += 1
    
    vocab = [w for w in answer_counts if answer_counts[w] >= th]



    return answer_counts, vocab, ques_depth

def CheckVocabTop(iterator, vocab, ques_depth):
    checkVocab = {}
    for sent in vocab:
        checkVocab[sent] = 0

    nsents = 0
    for sent in iterator:
        
        sent_string = ' '.join(sent[:ques_depth[nsents]])
        if sent_string in vocab:
            # check whether reach the max length of question.
            if len(sent) < ques_depth[nsents]+1:
                checkVocab[sent_string] = 1

        nsents += 1
    return checkVocab

def AnswerVocabTop(iterator, vocab, answer_counts, ques_depth, check_len, th):
    answer_counts_new = {}
    ques_depth_new = []

    nsents = 0
    for sent in iterator:
        sent_string = ' '.join(sent[:ques_depth[nsents]])
        if sent_string in vocab:
        # group the list to string. 
            if answer_counts[sent_string] > th and check_len[sent_string] == 0:
                sent_string_new = ' '.join(sent[:ques_depth[nsents]+1])

                answer_counts_new[sent_string_new] = answer_counts_new.get(sent_string_new, 0) + 1
                ques_depth_new.append(ques_depth[nsents]+1)    
            else:
                ques_depth_new.append(ques_depth[nsents])
        else:
            ques_depth_new.append(ques_depth[nsents])
    
        nsents += 1

    return answer_counts_new, ques_depth_new



def GetWord2VecVocab(vocab):
    # initialized the word2vec model.
    model = Word2Vec()
    wordtovec = {}
    count = 0

    for w in vocab:
        wordtovec[w], flag = model.getVec(w)
        if flag == 0:
            wordtovec[w] = (np.random.rand(300) - 0.5 ) / 300
        count = count + flag

    print '%d words find Word2Vec representation, %d words not' %(count, len(vocab)-count)
    return wordtovec

def BoWEncoding(iterator, wordtoix, word_order=0):

    histLen = len(wordtoix)
    Qencoder = []
    for sent in iterator:
    # for each question.
        vectmp = np.array(np.zeros(histLen))
        if word_order == 0:
            for w in sent:
            # for each word in question:
                idx = wordtoix.get(w, histLen)
                if idx != histLen:
                    vectmp[idx] = 1
        else:
            if len(sent) >= word_order:
                w = sent[word_order-1]
                idx = wordtoix.get(w, histLen)
                if idx != histLen:
                    vectmp[idx] = 1

        Qencoder.append(vectmp)
    return np.array(Qencoder)

def BoWEncodingTop(iterator, wordtoix, word_order=0):

    histLen = len(wordtoix)
    Qencoder = []
    for sent in iterator:
    # for each question.
        vectmp = np.array(np.zeros(histLen))
        if word_order == 0:
            for w in sent:
            # for each word in question:
                idx = wordtoix.get(w, histLen)
                if idx != histLen:
                    vectmp[idx] = 1
        else:
            if len(sent) >= word_order:
                for w in sent[:word_order-1]:
                    idx = wordtoix.get(w, histLen)
                    if idx != histLen:
                        vectmp[idx] = 1

        Qencoder.append(vectmp)
    return np.array(Qencoder)

def BoWAnswerEncodingVec(iterator, wordtoix):
    histLen = len(wordtoix) 
    Aencoder = []
    for sent in iterator:
        vectmp = np.array(np.zeros(histLen))
        sent_string = ' '.join(sent)
        idx = wordtoix.get(sent_string, histLen)
        if idx != histLen:
            vectmp[idx] = 1
        Aencoder.append(vectmp)
    return np.array(Aencoder)

def BoWAnswerEncoding(iterator, wordtoix):
    histLen = len(wordtoix) 
    Aencoder = []
    for sent in iterator:
        sent_string = ' '.join(sent)
        idx = wordtoix.get(sent_string, histLen)
        Aencoder.append(idx)
    return np.array(Aencoder)

def BOWMultiAnswerEncoding(iterator, wordtoix):
    histLen = len(wordtoix) 
    Aencoder = []
    for sent in iterator:
        multiAnswer = []
        for ans in sent:
            idx = wordtoix.get(ans, histLen)
            multiAnswer.append(idx)
        Aencoder.append(multiAnswer)
    return np.array(Aencoder)


def BOWMultiAnswerEncodingCheck(iterator, wordtoix, label, groups):
    histLen = len(wordtoix) 
    Aencoder = []
    count = 0
    for sent in iterator:
        if sent != []:
            multiAnswer = []
            for ans in sent:
                idx = wordtoix.get(ans, histLen)
                multiAnswer.append(idx)

            for group in groups:

                if sum(np.array(group) == count) == 1:
                    flag = 0
                    for idx in group:
                        if sum(np.array(multiAnswer)==label[count]):
                            flag = 1
                    if flag == 0:
                        print '%d' %count
                        print 'wrong %s', sent
        count += 1

    return np.array(Aencoder)


def IA2NAEncoding(iterator, wordtoix):
    histLen = len(wordtoix)
    Aencoder = []
    for group in iterator:
        vectmp = np.array(np.zeros(histLen))
        for sent in group:
            sent_string = ' '.join(sent)
            idx = wordtoix.get(sent_string, histLen)
            if idx != histLen:
                vectmp[idx] = 1
        Aencoder.append(vectmp)
    return np.array(Aencoder)


def GetTrainingVecLabel(Qencoder, Aencoder, wordtoix):
    histLen = len(wordtoix)     
    Avec = []
    Alabel = []
    Qvec = []
    count = 0
    for i in range(len(Aencoder)):
        count += 1
        if Aencoder[i]!= histLen:
            Alabel.append(Aencoder[i])
            Qvec.append(Qencoder[i])
    print 'The answers from %d to %d with %.2f' %(count, len(Alabel), np.float(len(Alabel))/count)
    return np.array(Qvec), np.array(Alabel)


def Word2VecEncoding(iterator, wordtovec):
    encoder = []
    ix = 0
    for sent in iterator:
        vectmp = np.array(np.zeros(300)) # the word2Vec is 300 dimension by default.
        for w in sent:
        # for each word in the question:
            # we initialized the random vector for each different question or caption.
            vectmp += wordtovec.get(w, 0)
        ave = vectmp / len(sent)
        encoder.append(ave)
        ix += 1

    return np.array(encoder)

def FindAnswerGroup(iterator):
    group = defaultdict(list)
    count = 0
    for sent in iterator:
        group[sent].append(count)
        count+=1

    pair = []
    for key, value in group.iteritems():
        pair.append(value)
    return pair    

def priorQuestion(dp, misc):

    misc['Qwordtoix1'], misc['Qixtoword1'], misc['Qvocab1'] = preProBuildWordVocab(dp.iterQuestion('train'),10, 1)
    misc['Qwordtoix2'], misc['Qixtoword2'], misc['Qvocab2'] = preProBuildWordVocab(dp.iterQuestion('train'),50, 2)

    bowQuestionTrain1 = BoWEncoding(dp.iterQuestion('train'), misc['Qwordtoix1'], 1)
    bowQuestionTrain2 = BoWEncoding(dp.iterQuestion('train'), misc['Qwordtoix2'], 2)

    bowQuestionTest1 = BoWEncoding(dp.iterQuestion('test'), misc['Qwordtoix1'], 1)
    bowQuestionTest2 = BoWEncoding(dp.iterQuestion('test'), misc['Qwordtoix2'], 2)

    bowQuestionTrain = np.concatenate((bowQuestionTrain1, bowQuestionTrain2), axis=1) 
    bowQuestionTest = np.concatenate((bowQuestionTest1, bowQuestionTest2), axis=1) 

    count = 0 
    for vec in bowQuestionTrain:
        if sum(vec) == 2:
            count += 1
    print 'Cover training sample %d with %.2f' % (count, np.float(count) / len(bowQuestionTrain))

    count = 0 
    for vec in bowQuestionTest:
        if sum(vec) == 2:
            count += 1
    print 'Cover testing sample %d with %.2f' % (count, np.float(count) / len(bowQuestionTest))
    
    return bowQuestionTrain, bowQuestionTest, misc['Qixtoword1'], misc['Qixtoword2']

def preQuestion(dp, misc):
    # get the vocabulary dictionary for question
    misc['Qwordtoix0'], misc['Qixtoword0'], misc['Qvocab0'] = preProBuildWordVocab(dp.iterQuestion('train'),1000, 0)
    misc['Qwordtoix1'], misc['Qixtoword1'], misc['Qvocab1'] = preProBuildWordVocab(dp.iterQuestion('train'),10, 1)
    misc['Qwordtoix2'], misc['Qixtoword2'], misc['Qvocab2'] = preProBuildWordVocab(dp.iterQuestion('train'),10, 2)
    misc['Qwordtoix3'], misc['Qixtoword3'], misc['Qvocab3'] = preProBuildWordVocab(dp.iterQuestion('train'),10, 3)

    # get the BOW encoding
    bowQuestionTrain0 = BoWEncoding(dp.iterQuestion('train'), misc['Qwordtoix0'], 0)
    bowQuestionTrain1 = BoWEncoding(dp.iterQuestion('train'), misc['Qwordtoix1'], 1)
    bowQuestionTrain2 = BoWEncoding(dp.iterQuestion('train'), misc['Qwordtoix2'], 2)
    bowQuestionTrain3 = BoWEncoding(dp.iterQuestion('train'), misc['Qwordtoix3'], 3)

    bowQuestionTest0 = BoWEncoding(dp.iterQuestion('test'), misc['Qwordtoix0'], 0)
    bowQuestionTest1 = BoWEncoding(dp.iterQuestion('test'), misc['Qwordtoix1'], 1)
    bowQuestionTest2 = BoWEncoding(dp.iterQuestion('test'), misc['Qwordtoix2'], 2)
    bowQuestionTest3 = BoWEncoding(dp.iterQuestion('test'), misc['Qwordtoix3'], 3)

    bowQuestionTrain = np.concatenate((bowQuestionTrain0, bowQuestionTrain1, bowQuestionTrain2, bowQuestionTrain3), axis=1) 
    bowQuestionTest = np.concatenate((bowQuestionTest0, bowQuestionTest1, bowQuestionTest2, bowQuestionTest3), axis=1) 

    return bowQuestionTrain, bowQuestionTest, misc


def preCaption(dp, misc):
    misc['Cwordtoix'], misc['Cixtoword0'], misc['Cvocab'] = preProBuildWordVocab(dp.iterCaption('train'),1000, 0)
    bowCaptionTrain = BoWEncoding(dp.iterCaption('train'), misc['Cwordtoix'], 0)
    bowCaptionTest = BoWEncoding(dp.iterCaption('test'), misc['Cwordtoix'], 0)
    
    return bowCaptionTrain, bowCaptionTest, misc

def preImage(dp, misc):
    dataset = 'coco'
    if misc['CNNfeat'] == 'fc7':
        cnnTrainPath = os.path.join('data', dataset, 'feat', 'decaf_train.npy')
        cnnTestPath = os.path.join('data', dataset, 'feat', 'decaf_val.npy')
    else:
        cnnTrainPath = os.path.join('data', dataset, 'feat', 'prob_decaf_train.npy')
        cnnTestPath = os.path.join('data', dataset, 'feat', 'prob_decaf_val.npy')       
    # Generate the train and test feature. 
    cnnTrain = np.load(cnnTrainPath)
    cnnTest = np.load(cnnTestPath)
    cnnTrain = np.concatenate((cnnTrain, cnnTest), axis=1)     
    ImgFeatTrain = []
    for ImgId in dp.iterImageId('train'):
        # find the corresponding position.
        ImgFeatTrain.append(cnnTrain[:1000,dp.list_train.index(ImgId)])

    ImgFeatTest = []
    for ImgId in dp.iterImageId('test'):
        ImgFeatTest.append(cnnTest[:1000,dp.list_val.index(ImgId)])

 
    return ImgFeatTrain, ImgFeatTest

def preQuestionImage(dp, misc):
    bowQuestionTrain,bowQuestionTest, misc = preQuestion(dp, misc)
    ImgFeatTrainReduce, ImgFeatTestReduce = preImage(dp, misc)
    
    QuesImgTrain = np.concatenate((bowQuestionTrain, ImgFeatTrainReduce), axis=1) 
    QuesImgTest = np.concatenate((bowQuestionTest, ImgFeatTestReduce), axis=1) 

    return QuesImgTrain, QuesImgTest, misc

def preQuestionCaption(dp, misc):
    bowQuestionTrain,bowQuestionTest, misc = preQuestion(dp, misc)
    bowCaptionTrain, bowCaptionTest, misc = preCaption(dp, misc)

    QuesCapTrain = np.concatenate((bowQuestionTrain, bowCaptionTrain), axis=1) 
    QuesCapTest = np.concatenate((bowQuestionTest, bowCaptionTest), axis=1)   

    return QuesCapTrain, QuesCapTest, misc

def preQuestionCaptionImg(dp, misc):
    bowQuestionTrain,bowQuestionTest, misc = preQuestion(dp, misc)
    bowCaptionTrain, bowCaptionTest, misc = preCaption(dp, misc)    
    ImgFeatTrainReduce, ImgFeatTestReduce = preImage(dp, misc)
    QuesCapImgTrain = np.concatenate((bowQuestionTrain, bowCaptionTrain, ImgFeatTrainReduce), axis=1) 
    QuesCapImgTest = np.concatenate((bowQuestionTest, bowCaptionTest, ImgFeatTestReduce), axis=1)   
    return QuesCapImgTrain, QuesCapImgTest, misc

def trainModel(trainVec, trainLable, testVec, input_num, hidden_num, epoch_num, misc, L1=0.00, L2=0.001):
    # get the label for the answer.
    train_x, train_y = GetTrainingVecLabel(trainVec, trainLable, misc['Awordtoix'])
    train_size = len(train_x)-misc['vali_size']
    
    train_data = (train_x[:train_size], train_y[:train_size])
    vali_data = (train_x[train_size:], train_y[train_size:])
    test_data = (trainVec[:2000], np.zeros(len(trainVec[:2000])))
    print 'start training MLP'
    out = test_mlp(train_data, vali_data, test_data, learning_rate=0.01, L1_reg=L1, L2_reg=L2, n_epochs=epoch_num,
             batch_size=100, n_input = input_num, n_hidden=hidden_num, n_output = misc['numAnswer'])  

    return out


def SVMtrainModel(trainVec, trainLable, testVec, misc):
    train_x, train_y = GetTrainingVecLabel(trainVec, trainLable, misc['Awordtoix'])    
    print 'Start training SVM'
    C = misc['C']
    clf = SVM(C)
    clf.train(train_x, train_y)
    out = clf.predictProb(testVec)

    # check whether out same as the label len
    if len(out[0]) != misc['numAnswer']:
        print "label number is not consistent.", sys.exc_info()[0]
        raise


    return out

def calAcc(out, misc):

    label_count = utils.mlpOPAcc(out, misc['bowAnswerTest'], misc['answerGroup'], misc['numAnswer'])
    utils.mlpMSAcc(out, misc['bowAnswerTest'], misc['answerGroup'], misc['multiAnswerTest'], misc['numAnswer'])

    print 'The statistics of label are %s' %(label_count)  

def calRandomAcc(misc):
    label_count = utils.mlpOPlable(np.zeros(len(misc['bowAnswerTest'])), misc['bowAnswerTest'], misc['answerGroup'], misc['numAnswer'])
    randintx=[randint(0,499) for p in range(len(misc['bowAnswerTest']))]
    utils.mlpOPlable(randintx, misc['bowAnswerTest'], misc['answerGroup'], misc['numAnswer'])



def openAnswerWriteJson(out, iterator, misc):
    # given the prediction output, write the result to json format.
    count = 0
    JsonData = []
    for imgId, ques, quesStr in iterator:
        subData = {}
        # find the label
        #label = out[count].index(max(out[count]))
        label = out[count]
        # find the answer corresponding to it.
        ans = misc['Aixtoword'].get(label, 'NA')
        subData['quesStr'] = quesStr
        subData['imgId'] = imgId
        subData['ans_a'] = [{'ansStr':ans}]
        subData['ques'] = ques
        JsonData.append(subData)
        count += 1
    
    # save with different name.
    ''' 
    if misc['classifier'] == 'MLP':
        savename = 'Open_'+ 'K_'+str(misc['numAnswer'])+ '_T_'+str(misc['Type'])+'_C_' + misc['classifier'] + '_I_' + misc['CNNfeat'] + '_C_' + str(misc['C'])
    else:
        savename = 'Open_'+ 'K_'+str(misc['numAnswer'])+ '_T_'+str(misc['Type'])+'_C_' + misc['classifier'] + '_I_' + misc['CNNfeat'] + '_H_' + str(misc['numHidden']) + '_L2_' + str(misc['L2'])

    '''
    savename = 'prior_baseline_' + str(misc['th'])
    savepath = os.path.join('Json', savename+'.json')
    with open(savepath, 'w') as outfile:
        json.dump(JsonData, outfile)

def multChoiceWriteJson(out, iterator, misc):
    # given the prediction output, write the result to json format.
    count = 0
    JsonData = []
    numAnswer = misc['numAnswer']
    for imgId, ques, quesStr in iterator:
        subData = {}
        # find the label
        choice = misc['multiAnswerTest'][count]
        if len(choice) > 0:
            selectScore = []
            for idx in choice:
                if idx != numAnswer:
                    selectScore.append(out[count][idx])
                else:
                    selectScore.append(0)
            label = choice[selectScore.index(max(selectScore))]
        
        else:
            label = numAnswer
        # find the answer corresponding to it.
        ans = misc['Aixtoword'].get(label, 'NA')
        subData['quesStr'] = quesStr
        subData['imgId'] = imgId
        subData['ans_a'] = [{'ansStr':ans}]
        subData['ques'] = ques
        JsonData.append(subData)
        count += 1

    if misc['classifier'] == 'MLP':
        savename = 'Mult_'+ 'K_'+str(misc['numAnswer'])+ '_T_'+str(misc['Type'])+'_C_' + misc['classifier'] + '_I_' + misc['CNNfeat'] + '_C_' + str(misc['C'])
    else:
        savename = 'Mult_'+ 'K_'+str(misc['numAnswer'])+ '_T_'+str(misc['Type'])+'_C_' + misc['classifier'] + '_I_' + misc['CNNfeat'] + '_H_' + str(misc['numHidden']) + '_L2_' +str(misc['L2'])

    savepath = os.path.join('Json', savename+'.json')
    with open(savepath, 'w') as outfile:
        json.dump(JsonData, outfile)
    # save with different name. 


def Prior_baseline(num_hidden=50, K = 500, Type = 0, isBinary=0, classifier = 'MLP', CNNfeat = 'fc7', L2 = 0.001, C = 1):
    # Type, a list indicate which we want to use. 
    dataset = 'coco'
    word_count_threshold = 1
    misc= {}  
    misc['C'] = C
    misc['Type'] = Type
    misc['IsBinary'] = isBinary
    misc['numAnswer'] = K
    misc['numHidden'] = num_hidden
    misc['vali_size'] = 20000
    misc['classifier'] =classifier
    misc['CNNfeat'] = CNNfeat
    misc['L2'] = L2 
    L1 = 0
    
    dp = getDataProvider(dataset, misc['IsBinary'])  
    print 'The K number is %d' %(misc['numAnswer'])
    #dp.downloadImage()
    #dp.loadCaption()

    # get the vocabulary for the answers.
    misc['Awordtoix'], misc['Aixtoword'], misc['Avocab'] = preProBuildAnswerVocab(dp.iterAnswer('train'),misc['numAnswer'])
    
    misc['bowAnswerTrain'] = BoWAnswerEncoding(dp.iterAnswer('train'), misc['Awordtoix'])
    misc['bowAnswerTest'] = BoWAnswerEncoding(dp.iterAnswer('test'), misc['Awordtoix'])
    misc['multiAnswerTest'] = BOWMultiAnswerEncoding(dp.iterMultiAnswer('test'), misc['Awordtoix'])
    misc['genCaptionTest'] = BOWMultiAnswerEncoding(dp.iterGenCaption('test'), misc['Awordtoix'])
    misc['answerGroup'] = FindAnswerGroup(dp.iterImgIdQuestion('test'))
    result = {}
    
    for misc['th'] in range(150, 400, 25):

        print 'th value is %d' %misc['th']
        answer_counts, vocab, ques_depth = preProBuildAnswerVocabTop(dp, misc['th'])

        idx = 0
        ans_counts = {}

        for sent in dp.iterQuestion('train'):
            string = ' '.join(sent[:ques_depth[idx]])
            if string in vocab:
                if ans_counts.get(string, misc['numAnswer']) == misc['numAnswer']:
                    ans_counts[string] = [misc['bowAnswerTrain'][idx]]
                else:
                    ans_counts[string] = ans_counts.get(string, misc['numAnswer']) + [misc['bowAnswerTrain'][idx]]
            idx += 1

        # get the prior of the label
        ans_prior = {}
        for key, value in ans_counts.iteritems():
            tmp = {}
            for idx in value:
                tmp[idx] = tmp.get(idx, 0) + 1
            tmp_idx = sorted(tmp, key=tmp.get, reverse=True)[0]

            ans_prior[key] = misc['Aixtoword'].get(tmp_idx)

        for i in range(6):
            print "Depth %d" %(i+1)
            for key, value in sorted(ans_counts.iteritems(), key=lambda (k,v): (v,k)):
                if len(key.split(' '))==i+1:
                    print "%s: %s   " % (key, len(value)),
            print ""
        
        for i in range(6):
            print "Depth %d" %(i+1)
            for tmp in vocab:
                if len(tmp.split(' '))==i+1:
                    print "%s: %s   " % (tmp, ans_prior.get(tmp)), 
            print ""

        depth_count = {}
        for tmp in vocab:
            count = len(tmp.split(' '))
            depth_count[count] = depth_count.get(count, 0) + 1

        pdb.set_trace()
        max_depth = max(ques_depth)

        ans = []
        for sent in dp.iterQuestion('test'):
            # iter from big to small
            tmp = ''
            for depth in range(max_depth):
                string = ' '.join(sent[:ques_depth[max_depth - depth]])

                if string in vocab:
                    tmp = string
                    break


            if tmp != '':
                idx = misc['Awordtoix'].get(ans_prior.get(string))
                ans.append(idx)
            else:
                ans.append(0)
        
        utils.mlpOPlable(ans, misc['bowAnswerTest'], misc['answerGroup'], misc['numAnswer'])

        openAnswerWriteJson(ans, dp.iterAll('test'), misc)



def main(num_hidden=50, K = 150, Type = 1, isBinary=0, classifier = 'MLP', CNNfeat = 'softmax', L2 = 0.0005, C = 1):
    # Type, a list indicate which we want to use. 
    dataset = 'coco'
    word_count_threshold = 1
    misc= {}  
    misc['C'] = C
    misc['Type'] = Type
    misc['IsBinary'] = isBinary
    misc['numAnswer'] = K
    misc['numHidden'] = num_hidden
    misc['vali_size'] = 25000
    misc['classifier'] =classifier
    misc['CNNfeat'] = CNNfeat
    misc['L2'] = L2 
    L1 = 0
    
    dp = getDataProvider(dataset, misc['IsBinary'])  
    print 'The K number is %d' %(misc['numAnswer'])
    #dp.downloadImage()
    #dp.loadCaption()

    # get the vocabulary for the answers.
    misc['Awordtoix'], misc['Aixtoword'], misc['Avocab'] = preProBuildAnswerVocab(dp.iterAnswer('train'),misc['numAnswer'])
    
    misc['bowAnswerTrain'] = BoWAnswerEncoding(dp.iterAnswer('train'), misc['Awordtoix'])
    misc['bowAnswerTest'] = BoWAnswerEncoding(dp.iterAnswer('test'), misc['Awordtoix'])
    misc['multiAnswerTest'] = BOWMultiAnswerEncoding(dp.iterMultiAnswer('test'), misc['Awordtoix'])
    misc['genCaptionTest'] = BOWMultiAnswerEncoding(dp.iterGenCaption('test'), misc['Awordtoix'])
    misc['answerGroup'] = FindAnswerGroup(dp.iterImgIdQuestion('test'))
    result = {}
    

    if Type==0:
        print '===================================================='
        print 'Test on Question, The K number is %d' %(misc['numAnswer'])
        print '===================================================='

        trainVec, testVec = preQuestion(dp, misc)
        if misc['classifier'] == 'SVM':
            out = SVMtrainModel(trainVec, misc['bowAnswerTrain'], testVec, misc)
        else:
            out = trainModel(trainVec, misc['bowAnswerTrain'], testVec, 1030, misc['numHidden'], 300, misc, L1, L2)     
        calAcc(out, misc)
        multChoiceWriteJson(out, dp.iterAll('test'), misc)
        openAnswerWriteJson(out, dp.iterAll('test'), misc)          
    if Type==1:
        print '===================================================='
        print 'Test on QuestionImage, The K number is %d' %(misc['numAnswer'])
        print '===================================================='

        trainVec, testVec, misc = preQuestionImage(dp, misc)

        Vocab_save = {}
        Vocab_save['Awordtoix'] = misc['Awordtoix']
        Vocab_save['Aixtoword'] = misc['Aixtoword']
        Vocab_save['Avocab'] = misc['Avocab']
        Vocab_save['Qwordtoix0'] = misc['Qwordtoix0']
        Vocab_save['Qwordtoix1'] = misc['Qwordtoix1']
        Vocab_save['Qwordtoix2'] = misc['Qwordtoix2']
        Vocab_save['Qwordtoix3'] = misc['Qwordtoix3']

        utils.pickleSave('Vocab', Vocab_save)

        if misc['classifier'] == 'SVM':
            out = SVMtrainModel(trainVec, misc['bowAnswerTrain'], testVec,misc)
        else:
            out = trainModel(trainVec, misc['bowAnswerTrain'], testVec, 2030, misc['numHidden'], 300, misc, L1, L2)
        
        calAcc(out, misc)
        multChoiceWriteJson(out, dp.iterAll('test'), misc)
        openAnswerWriteJson(out, dp.iterAll('test'), misc)      
    if Type == 2:
        print '===================================================='
        print 'Test on Caption, The K number is %d' %(misc['numAnswer'])
        print '===================================================='

        trainVec, testVec = preCaption(dp, misc)
        if misc['classifier'] == 'SVM':
            out = SVMtrainModel(trainVec, misc['bowAnswerTrain'], testVec,misc)
        else:
            out = trainModel(trainVec, misc['bowAnswerTrain'], testVec, 1000, misc['numHidden'], 300, misc, L1, L2)
        calAcc(out, misc)  
        multChoiceWriteJson(out, dp.iterAll('test'), misc)
        openAnswerWriteJson(out, dp.iterAll('test'), misc)  
    if Type==3:
        print '===================================================='
        print 'Test on Image, The K number is %d' %(misc['numAnswer'])
        print '===================================================='

        trainVec, testVec = preImage(dp, misc)
        if misc['classifier'] == 'SVM':
            out = SVMtrainModel(trainVec, misc['bowAnswerTrain'], testVec,misc)
        else:
            out = trainModel(trainVec, misc['bowAnswerTrain'], testVec, 1000, misc['numHidden'], 300, misc, L1, L2)
        calAcc(out, misc)         
        multChoiceWriteJson(out, dp.iterAll('test'), misc)
        openAnswerWriteJson(out, dp.iterAll('test'), misc)   
    if Type == 4:
        print '===================================================='
        print 'Test on QuestionCaption, The K number is %d' %(misc['numAnswer'])
        print '===================================================='

        trainVec, testVec = preQuestionCaption(dp, misc)
        if misc['classifier'] == 'SVM':
            out = SVMtrainModel(trainVec, misc['bowAnswerTrain'], testVec,misc)
        else:
            out = trainModel(trainVec, misc['bowAnswerTrain'], testVec, 2030, misc['numHidden'], 300, misc, L1, L2)
        calAcc(out, misc)    
        multChoiceWriteJson(out, dp.iterAll('test'), misc)
        openAnswerWriteJson(out, dp.iterAll('test'), misc)  
    if Type==5:
        print '===================================================='
        print 'Test on QuestionImageCaption, The K number is %d' %(misc['numAnswer'])
        print '===================================================='

        trainVec, testVec = preQuestionCaptionImg(dp, misc)
        if misc['classifier'] == 'SVM':
            out = SVMtrainModel(trainVec, misc['bowAnswerTrain'], testVec,misc)
        else:
            out = trainModel(trainVec, misc['bowAnswerTrain'], testVec, 3030, misc['numHidden'], 300, misc, L1, L2)
        multChoiceWriteJson(out, dp.iterAll('test'), misc)
        openAnswerWriteJson(out, dp.iterAll('test'), misc) 
        calAcc(out, misc)     

'''
# run the function
print ' num_hidden = ' + sys.argv[1],
print ' K = ' + sys.argv[2],
print ' Type = ' + sys.argv[3], 
print ' isBinary = ' + sys.argv[4],
print ' classifier = ' + sys.argv[5],
print ' CNNfeat = ' + sys.argv[6],
print ' L2 = ' + sys.argv[7],
print ' C = ' + sys.argv[8]

num_hidden = int(sys.argv[1])
K = int(sys.argv[2])
Type = int(sys.argv[3])
isBinary = int(sys.argv[4])
classifier = sys.argv[5]
CNNfeat = sys.argv[6]
L2 = float(sys.argv[7])
C = float(sys.argv[8])

main(num_hidden, K , Type , isBinary, classifier, CNNfeat, L2, C)
'''

main()
# Prior_baseline()
