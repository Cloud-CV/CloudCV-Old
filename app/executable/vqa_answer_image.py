# VQA for CloudCV
# author: Jiasen Lu, Devi Parikh, Clint

import numpy as np
import os
import sys
import pdb
import time
import pickle
import operator

import scipy.io
from collections import defaultdict
from random import randint
from vqa_files.MLP_test import mlp_test
from vqa_files import utils


from app.celery.celery.celery import celery

dataFolder = '/home/ubuntu/cloudcv/cloudcv17/app/executable/vqa_files/data'

def BoWEncoding(sent, wordtoix, word_order=0):
    # given the sent string (already token), return BOW encoding.

    histLen = len(wordtoix)
    Qencoder = []
    
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

def genTokens(sent):
    tokens = []
    tmp = sent.lower().split()
    # only get the words.
    for token in tmp:
        tokens.append(''.join(c for c in token if c.isalpha() or c.isdigit()))
    return tokens

@celery.task
def vqa_answer(imgFeatPath, sent):
    imgFeat = np.load(imgFeatPath)

    dataset = 'coco'
    # Load the Vocabulary
    VocabPath = os.path.join(dataFolder, dataset, 'model', 'Vocab')
    Vocab = utils.pickleLoad(VocabPath)
    # Load the model
    ModelPath =  os.path.join(dataFolder, dataset, 'model', 'model')
    Model = utils.pickleLoad(ModelPath)

    sent = genTokens(sent)
    bowQuestionTest0 = BoWEncoding(sent, Vocab['Qwordtoix0'], 0)
    bowQuestionTest1 = BoWEncoding(sent, Vocab['Qwordtoix1'], 1)
    bowQuestionTest2 = BoWEncoding(sent, Vocab['Qwordtoix2'], 2)
    bowQuestionTest3 = BoWEncoding(sent, Vocab['Qwordtoix3'], 3)

    bowQuestionTest = np.concatenate((bowQuestionTest0, bowQuestionTest1, bowQuestionTest2, bowQuestionTest3), axis=1) 
    
    testVec = np.concatenate((bowQuestionTest, [imgFeat]), axis=1) 
    test_data = (testVec, 0)

    out = mlp_test(test_data, Model)
    tmp = out[0]
    label_set = sorted(range(len(tmp)),key=lambda x: tmp[x], reverse = True)[:5]
    label_score = sorted(tmp, reverse = True)[:5]

    ans = []
    for i in range(0, len(label_set)):
        ans.append([Vocab['Aixtoword'].get(label_set[i], 'NA'), label_score[i]])
    return ans
