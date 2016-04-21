
import traceback
import redis
import os
os.environ['THEANO_FLAGS'] = 'optimizer=None,exception_verbosity=high, device=gpu'
import pdb

#   from app.celery.celery.celery import celery

import numpy as np

import json
import pickle
np.random.seed(1234)

from keras.preprocessing import sequence, text
from keras.utils import np_utils
from keras.layers.core import *


dataFolder = '/home/ubuntu/cloudcv/cloudcv17/app/executable/vqa_files/data'

qtok_path = '/home/ubuntu/cloudcv/cloudcv17/app/executable/LSTM+MLP/vocab.pkl'
ans_voc_path = '/home/ubuntu/cloudcv/cloudcv17/app/executable/LSTM+MLP/top_ans_1000.json'
model_path = '/home/ubuntu/cloudcv/cloudcv17/app/executable/LSTM+MLP/model_cloudCV.pkl'

# Question tokenizer
f = file(qtok_path, 'rb')
qtok = pickle.load(f)
f.close()

# Answer tokenizer
def nothing_filter():
    f = ''
    return f

ans_voc_raw = json.load(open(ans_voc_path, 'r'))
ans_voc = [w.encode('utf-8') for w in ans_voc_raw]
atok = text.Tokenizer(nb_words = None, filters = nothing_filter(), lower=True, split='~')
atok.fit_on_texts(ans_voc)
a_word_idx = atok.word_index

# Load Model here once!
f = file(model_path, 'rb')
model = pickle.load(f)
f.close()

import re
import json
import string

contractions = {"aint": "ain't", "arent": "aren't", "cant": "can't", "couldve": "could've", "couldnt": "couldn't", "couldn'tve": "couldn't've", "couldnt've": "couldn't've", "didnt": "didn't", "doesnt": "doesn't", "dont": "don't", "hadnt": "hadn't", \
    "hadnt've": "hadn't've", "hadn'tve": "hadn't've", "hasnt": "hasn't", "havent": "haven't", "hed": "he'd", "hed've": "he'd've",
    "he'dve": "he'd've", "hes": "he's", "howd": "how'd", "howll": "how'll", "hows": "how's", "Id've": "I'd've", "I'dve": "I'd've",
    "Im": "I'm", "Ive": "I've", "isnt": "isn't", "itd": "it'd", "itd've": "it'd've", "it'dve": "it'd've", "itll": "it'll", "let's": "let's",
    "maam": "ma'am", "mightnt": "mightn't", "mightnt've": "mightn't've", "mightn'tve": "mightn't've", "mightve": "might've",
    "mustnt": "mustn't", "mustve": "must've", "neednt": "needn't", "notve": "not've", "oclock": "o'clock", "oughtnt": "oughtn't",
    "ow's'at": "'ow's'at", "'ows'at": "'ow's'at", "'ow'sat": "'ow's'at", "shant": "shan't", "shed've": "she'd've", "she'dve": "she'd've",
    "she's": "she's", "shouldve": "should've", "shouldnt": "shouldn't", "shouldnt've": "shouldn't've", "shouldn'tve": "shouldn't've",
    "somebody'd": "somebodyd", "somebodyd've": "somebody'd've", "somebody'dve": "somebody'd've", "somebodyll": "somebody'll",
    "somebodys": "somebody's", "someoned": "someone'd", "someoned've": "someone'd've", "someone'dve": "someone'd've",
    "someonell": "someone'll", "someones": "someone's", "somethingd": "something'd", "somethingd've": "something'd've",
    "something'dve": "something'd've", "somethingll": "something'll", "thats": "that's", "thered": "there'd", "thered've": "there'd've",
    "there'dve": "there'd've", "therere": "there're", "theres": "there's", "theyd": "they'd", "theyd've": "they'd've",
    "they'dve": "they'd've", "theyll": "they'll", "theyre": "they're", "theyve": "they've", "twas": "'twas", "wasnt": "wasn't",
    "wed've": "we'd've", "we'dve": "we'd've", "weve": "we've", "werent": "weren't", "whatll": "what'll", "whatre": "what're",
    "whats": "what's", "whatve": "what've", "whens": "when's", "whered": "where'd", "wheres": "where's", "whereve": "where've",
    "whod": "who'd", "whod've": "who'd've", "who'dve": "who'd've", "wholl": "who'll", "whos": "who's", "whove": "who've", "whyll": "why'll",
    "whyre": "why're", "whys": "why's", "wont": "won't", "wouldve": "would've", "wouldnt": "wouldn't", "wouldnt've": "wouldn't've",
    "wouldn'tve": "wouldn't've", "yall": "y'all", "yall'll": "y'all'll", "y'allll": "y'all'll", "yall'd've": "y'all'd've",
    "y'alld've": "y'all'd've", "y'all'dve": "y'all'd've", "youd": "you'd", "youd've": "you'd've", "you'dve": "you'd've",
    "youll": "you'll", "youre": "you're", "youve": "you've"}

manualMap = { 'none': '0', 'zero': '0', 'one': '1',
    'two': '2',
    'three': '3',
    'four': '4',
    'five': '5',
    'six': '6',
    'seven': '7',
    'eight': '8',
    'nine': '9',
    'ten': '10'
}

articles = ['a', 'an', 'the']


periodStrip = re.compile("(?!<=\d)(\.)(?!\d)")
commaStrip = re.compile("(\d)(\,)(\d)")
punct = [';', r"/", '[', ']', '"', '{', '}', '(', ')', '=', '+', '\\', '_', '-', '>', '<', '@', '`', ',', '?', '!']

def processDigitArticle(inText):
    try:
        outText = []
        tempText = inText.lower().split()
        for word in tempText:
            word = manualMap.setdefault(word, word)
            if word not in articles:
                outText.append(word)
            else:
                pass
        for wordId, word in enumerate(outText):
            if word in contractions:
                outText[wordId] = contractions[word]
        outText = [outtext.decode('ascii', 'ignore') for outtext in outText]
        outText = ' '.join(outText)
        return outText
    except Exception as e:
        import traceback
        print traceback.format_exc()
        pdb.set_trace()

def processPunctuation(inText):
    outText = inText
    for p in punct:
        if (p + ' ' in inText or ' ' + p in inText) or (re.search(commaStrip, inText) != None):
            outText = outText.replace(p, '')
        else:
            outText = outText.replace(p, ' ')
    outText = periodStrip.sub("",outText,re.UNICODE)
    return outText

def process_string(instring):
    resAns = instring.replace('\n', ' ')
    resAns = resAns.replace('\t', ' ')
    resAns = resAns.strip()
    resAns = processPunctuation(resAns)
    resAns = processDigitArticle(resAns)
    return resAns

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def vqa_answer2(imgFeat, question, imageid, socketid):
    imgFeat = np.asarray([imgFeat])

    ques = process_string(question).encode('utf-8')
    print "Ques:", ques
    print "imgFeat Shape:", imgFeat.shape
    train_q_toked = qtok.texts_to_sequences([ques])
    q_word_index = qtok.word_index
    train_q_toked = sequence.pad_sequences(train_q_toked, maxlen = 20)
    print "train token:", train_q_toked.shape

    # max_question_features = len(q_word_index.keys()) + 1
    train_q_toked = np.asarray(train_q_toked)
    predictions = model.predict([train_q_toked, imgFeat])
    print predictions
    predicted_classes = np_utils.categorical_probas_to_classes(predictions)
    label_set = sorted(range(len(predictions[0])),key=lambda x: predictions[0][x], reverse=True)[:5]
    a_word_rev = dict ((v,k) for k, v in a_word_idx.items())

    ans = []
    for i in range(5):
        idx = label_set[i] + 1
        ans.append([a_word_rev[idx], predictions[0][idx - 1]])
        print 'The Top %d predict Answer is : %s, with score %.6f' %(i, a_word_rev[idx], predictions[0][idx - 1])

    web_result = {}
    web_result[imageid] = ans
    r.publish('result-rest', json.dumps({'web_result': web_result}))
    r.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))

    return ans


def test(imgFeatures, question, imageid, socketid):
    print "hello"
    # print imgFeatures
    print np.array(imgFeatures).shape
    print question
    return vqa_answer2(np.array(imgFeatures), question, imageid, socketid)

import redis
import threading
import time
class Listener(threading.Thread):
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)

    def run(self):

        for item in self.pubsub.listen():
            try:
                data = json.loads(item['data'])
                imageid = data['imageid']
                socketid = data['socketid']
                test(data['imgFeatures'], data['question'], imageid, socketid)
                time.sleep(0.01)
            except Exception as e:
                print str(traceback.format_exc(e))

if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, db=0)
    client = Listener(r, ['test_aws'])
    client.start()

    # r.publish('test', 'KILL')
