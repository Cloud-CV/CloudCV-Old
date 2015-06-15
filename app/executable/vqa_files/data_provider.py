import json
import os
import random
import scipy.io
import codecs
from collections import defaultdict
import urllib2
import pdb
import time
import numpy as np
import sys

class DataProvider:
    def __init__(self, dataset, IsBinary):
        print 'Initializing the data provider for the dataset'
        self.dataset_root = os.path.join('data', dataset)
        self.image_root = os.path.join('data', dataset, 'imgs')
        # load the dataset into memory
        dataset_path = os.path.join(self.dataset_root, 'mscoco_both_with_img.min.json')
        print 'BasicDataProvider: reading %s' % (dataset_path, )
        self.dataset = json.load(open(dataset_path, 'r'))
        if IsBinary==1:
            self.filterYesNo()
        
        imgPair = self.genPair('img')
        #self.withCaption = self.loadCaption()
        self.imgPair = imgPair
        self.genSplit(imgPair)

        # transform back from pair
        caption_path = os.path.join(self.dataset_root, 'coco_caption_new.json')
        print 'BasicDataProvider: reading %s' % (caption_path, )
        self.caption = json.load(open(caption_path, 'r'))
        
        # multi-question answer path
        multiAnswer_path = os.path.join(self.dataset_root, 'mscoco_multiple_choice_answers_fullscale.json')
        print 'BasicDataProvider: reading %s' % (multiAnswer_path, )
        multiAnswer = json.load(open(multiAnswer_path, 'r'))

        genCaption_path = os.path.join(self.dataset_root, 'genCaption.json')
        print 'BasicDataProvider: reading %s' % (genCaption_path, )
        self.genCaption = json.load(open(genCaption_path, 'r'))
        
        list_train_path = os.path.join(self.dataset_root, 'list_train.json')
        self.list_train = json.load(open(list_train_path, 'r'))
        list_val_path = os.path.join(self.dataset_root, 'list_val.json')
        self.list_val = json.load(open(list_val_path, 'r'))
        self.list_train = self.list_train + self.list_val
        # index with the multi asnwer and filter without the key 'multipleAns'
        self.multiAnswer = defaultdict(list)
        count = 0
        for img in multiAnswer:

            key1 = ' '.join(self.genTokens(img['quesStr'])) + img['img']

            if img.has_key('multipleAns'):
                count += 1
                self.multiAnswer[key1].append(img)

        print 'Processing Multi choice answer from %d to %d' %(len(multiAnswer), count)
        dataset = []
        for img in imgPair:
            for idx in img:
                dataset.append(idx)

        self.split = defaultdict(list)
        for img in dataset:
            self.split[img['split']].append(img)

        print 'The training number is %d, and the testing number is %d' %(len(self.split['train']), 
            len(self.split['test']))


#        answerNoImg_path = os.path.join(self.dataset_root, 'answer_without_img.json')
#        self.answerNoImg = json.load(open(answerNoImg_path, 'r'))
        
#        self.QuePairImg, self.QuePairNoImg = self.genQuestionPair(self.dataset, self.answerNoImg)

    def _getSentence(self, sent):
        return sent

    def loadCaption(self):
        print 'Loading the caption annotation'
        caption_train_path =  os.path.join(self.dataset_root, 'captions_train2014.json')
        caption_val_path =  os.path.join(self.dataset_root, 'captions_val2014.json')

        caption_train = json.load(open(caption_train_path, 'r'))
        caption_val =  json.load(open(caption_val_path, 'r'))
        
        # find the corresponding caption.
        pairTmp = defaultdict(list)
        for img in self.train:
            pairTmp[img['img']].append(img)
        for img in self.test:
            pairTmp[img['img']].append(img)

        captionTmp = []
        count = 0
        
        for key, value in pairTmp.iteritems():
            imgId = int(key[-10:-4])
            trainval = key[5:8]

            if trainval == 'val':
                for cap in caption_val['annotations']:
                    if imgId == cap['image_id']:
                        captionTmp.append({'img':key, 'caption': cap['caption']})
            else:
                for cap in caption_train['annotations']:
                    if imgId == cap['image_id']:
                        captionTmp.append({'img':key, 'caption': cap['caption']})
            print count
            count += 1

        pairTmp = defaultdict(list)
        for img in captionTmp:
            pairTmp[img['img']].append(img['caption'])
        self.writeJson(pairTmp, 'coco_caption_new.json')

    def filterYesNo(self):
        count = 0
        dataset = []
        for img in self.dataset:
            tmp = ' '.join(img['ans'])
            if  tmp == 'yes' or tmp =='no':
                dataset.append(img)
            count += 1
        self.dataset = dataset
        print 'After filtering Yes No, there are %d left' %(len(self.dataset))


    def genTokens(self, sent):
        tokens = []
        tmp = sent.lower().split()
        # only get the words.
        for token in tmp:
            tokens.append(''.join(c for c in token if c.isalpha() or c.isdigit()))
        return tokens

    def genPair(self, key='img'):
        pairTmp = defaultdict(list)
        for img in self.dataset:
            pairTmp[img[key]].append(img)
        
        #transform the imgPair dictionay to list
        pair = []
        for key, value in pairTmp.iteritems():
            pair.append(value)
        return pair
    
    def genQuestionPair(self, data1, data2):


        pairTmp1 = defaultdict(list)
        pairTmp2 = defaultdict(list)
        for i in range(len(data1)):

            key1 = ''.join(data1[i]['img'])+''.join(data1[i]['ques'])
            key2 = ''.join(data2[i]['img'])+''.join(data2[i]['ques'])
            if key1 == key2:
                pairTmp1[key1].append(data1[i])
                pairTmp2[key2].append(data2[i])
            else:
                print "The sequence order between IA and NI is different.", sys.exc_info()[0]
                raise
        #transform the imgPair dictionay to list
        pair1 = []
        for key, value in pairTmp1.iteritems():
            pair1.append(value)
        pair2 = []
        for key, value in pairTmp2.iteritems():
            pair2.append(value)

        return pair1, pair2

    def genSplit(self, pair):
        imgNum = len(pair)

        for i in range(imgNum):
            '''
            if pair[i][0]['img'][5:8] == 'val':

                label = 'test'
            else:
                label = 'train'
            '''
            label = 'train'
            for j in range(len(pair[i])):
                pair[i][j].update({'split':label})


    def genRandomSplit(self, pair, random, frac = 0.7):
        # generate the split of trainning set and testing set label.
        # pair could be image pair
        imgNum = len(pair)
        if random == 1:
            randNum = np.random.permutation(range(imgNum))
        else:
            randNum = np.array(range(imgNum))

        for i in range(imgNum):
            for j in range(len(pair[i])):
                pair[i][j].update({'split':'test'})

        for i in randNum[range(int(round(imgNum * frac)))]:
            for j in range(len(pair[i])):
                pair[i][j].update({'split':'train'})
        return pair
    '''
    def nlpGenLemmas(self, sent):
    # this funcion use the Stanford nlp, if we want to do paser, could use this as extractor.
    # note: we shoud add pause(0.1) if include this function in a loop.
        nlp = tool.StanfordNlp()
        nlp.getSentence(sent)
        nlp.getLemmas()
        pause(0.05) # wait enough time for the channel.
        return nlp.lemmas
    '''

    def iterImgIdQuestion(self, split='train'):
        for img in self.split[split]:
            yield ''.join(img['img'])+''.join(img['ques'])
    
    def iterAnswerPerQuestion(self, data):
        for ques in data:
            answer = []
            for ans in ques:
                answer.append(self.genTokens((ans['ans'])))
            yield answer

    def iterAnswerNoImage(self):
        # notice !! iter all the data, the sequence is different with other iteration.
        for img in self.answerNoImg:
            yield img['ans']

    def iterImageId(self, split='train'):
        for img in self.split[split]:
            yield img['img']    

    def iterQuestion(self, split='train'):
    # iter the question and get the tokens.
        for img in self.split[split]:
            yield img['ques']

    def iterAnswer(self, split='train'):
    # iter the answer and get the tokens.
        for img in self.split[split]:
            yield img['ans']
    
    def iterCaption(self, split='train'):
        for img in self.split[split]:
            yield self.genTokens(self.caption[img['img']][0])

    def iterMultiAnswer(self, split='train'):
        # we should transform the data and the index should be the image and question string 
        # in order to make it unique.
        for img in self.split[split]:
            key = ' '.join(img['ques']) + img['img']
            if len(self.multiAnswer[key]) > 0:
                yield self.multiAnswer[key][0]['multipleAns']
            else:
                yield []

    def iterGenCaption(self, split='test'):
        for img in self.split[split]:
            if self.genCaption.has_key(img['img']):
                yield self.genTokens(self.genCaption[img['img']][0])
            else:
                yield []


    def iterAll(self, split='test'):
        for img in self.split[split]:
            imgId = img['img']
            ques = img['ques']
            quesStr = img['quesStr']

            yield imgId, ques, quesStr

    def writeJson(self, data, name):
        with open(os.path.join(self.dataset_root, name), 'w') as outfile:
            json.dump(data, outfile)

    def downloadImage(self):
        # given the image name and download the image from server. 	
        print 'Start to download the image'
        pairTmp = defaultdict(list)
        for img in self.dataset:
            pairTmp[img['url']+img['img']].append(img)
        for img in pairTmp.values():
            URL = img[0]['url'] + img[0]['img']
            u = urllib2.urlopen(URL)
            h = u.info()
            totalSize = int(h["Content-Length"])
            print 'Downloading image %s with %s bytes' % (img[0]['img'],totalSize,)
            fp = open(os.path.join(self.image_root, img[0]['img']), 'wb')

            blockSize = 8192
            count = 0
            while True:
                chunk = u.read(blockSize)
                if not chunk: break
                fp.write(chunk)
                count += 1
                if totalSize > 0:
                    percent = int(count * blockSize * 100 / totalSize)
                if percent > 100: percent = 100
                print "%2d%%" % percent,
                if percent < 100:
                    print "\b\b\b\b\b",  # Erase "NN% "
                else:
                    print "Done."

            fp.flush()
            fp.close()

def getDataProvider(dataset, IsBinary=0):
	assert dataset in ['coco'], 'dataset %s unknown' % (dataset, )
	return DataProvider(dataset, IsBinary)