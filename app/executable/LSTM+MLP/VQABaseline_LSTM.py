import numpy as np
import theano
import json
import cPickle as pickle
import random
import sys
np.random.seed(1234)

import keras
from keras.preprocessing import sequence, text
from keras.optimizers import SGD, RMSprop, adagrad
from keras.utils import np_utils
from keras.models import Sequential, Graph
from keras.layers.core import *
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, GRU
from keras.layers.convolutional import Convolution2D,MaxPooling2D
from keras.callbacks import ModelCheckpoint
import pandas as pd
import os
import pdb

dataDir = '/home/harsh/visualAttention/VQA'
sys.path.append('/var/www/html/visualAttention/database')
sys.path.append(dataDir)
sys.path.append(os.path.join(dataDir, 'PythonEvaluationTools/vqaEvaluation'))
sys.path.append(os.path.join(dataDir, 'PythonHelperTools/vqaTools'))
sys.path.append('/home/harsh/visualAttention/vqalib/PreProcess')
sys.setrecursionlimit(10000)

# from database import *
# VQA Imports
from vqa import VQA
from vqa_utils import process_string
from vqaEval import VQAEval

def nothing_filter():
    f = '';
    return f
# Store a bunch of path that are needed. Some of them are not required.
# TODO: Remove paths not required.
class Config:
	def __init__(self):
		self.ans_num = 1000
		self.embedding_num = 200
		self.dim_question = 1024
		self.dim_caffe = 1024
		self.batch_size = 64
		self.nb_epoch = 20
		self.nhidden1 = 1024
		self.data_path = '/srv/share/Jiasen_code'
		self.img_path = os.path.join(self.data_path, 'data/vgg_fc7_feat/')
		self.ans_voc_path = '/srv/share/visualAttention/data/top_ans_'+ str(self.ans_num) +'.json'
		self.train_path = os.path.join(self.data_path, 'data/Old/LSTM/QAPair_'+ str(self.ans_num) +'_train2014_train.json')
		self.val_path = os.path.join(self.data_path, 'data/Old/LSTM/QAPair_'+ str(self.ans_num) +'_val2014_val.json')
		self.train_feat_path = self.img_path + 'train2014_fc7.npy'
		self.val_feat_path = self.img_path + 'val2014_fc7.npy'
		self.model_path = "/srv/share/visualAttention/model_cloudCV.pkl"
		self.df_path = '/srv/share/data/visualAttention.pkl'
		self.qtok_file_path = '/srv/share/visualAttention/data/vocab.pkl'

# Model file. Not using it for predicting. Loading from pickle instead.
class Model:
	def __init__(self, max_question_features, max_answer_features, config):
		print "Starting Compiling Model..."
		left = Sequential()
		left.add(Embedding(max_question_features, config.embedding_num));
		left.add(LSTM(config.embedding_num,config.dim_question)) #, return_sequences=True))

		right = Sequential()
		right.add(Dense(4096, config.dim_caffe))
		right.add(Activation('tanh'))
		self.model = Sequential()
		self.model.add(Merge([left, right], mode='mul'))
		self.model.add(Activation('tanh'))
		self.model.add(Dropout(0.5))
		self.model.add(Dense(config.dim_question, config.nhidden1))
		self.model.add(Activation('tanh'))
		self.model.add(Dropout(0.5))	
		self.model.add(Dense(config.nhidden1, max_answer_features))
		self.model.add(Activation("softmax"))
		keras.optimizers.RMSprop(lr=0.00001, rho=0.9, epsilon=1e-6)
		self.model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
		print "Compilation Done."

# VQA Baseline: LSTM + MLP
class VQABaseline_LSTM:

	def __init__(self, configuration=None):
		if configuration is None:
			self.config = Config()
		else:
			print "Using the given configuration"
			self.config = configuration
		
		print "Generating Question Tokenizer from Training questions"
		ques_voc = self.loadQuestionVocabulary()
		self.qtok = self.loadQuestionTokenizer()

		print "Generating Answer Tokenizer"
		ans_voc = self.loadAnswerVocabulary()
		self.atok = self.getAnswerTokenizer(ans_voc)

		max_question_features = len(self.qtok.word_index.keys()) + 1
		max_answer_features = len(self.atok.word_index.keys())
		print "Loading Model"
		self.loadModel()
		print "Done!"
		# self.modelObj = Model(max_question_features,max_answer_features, self.config)

	def loadQuestionVocabulary(self, question_path=None):
		if question_path is None:
			question_path = self.config.train_path
		
		# form question vocabulary from training questions
		train_data_raw = json.load(open(self.config.train_path, 'r'))
		ques_voc = []
		for i in range(len(train_data_raw)):
			ques_voc.append(train_data_raw[i][1].encode('utf-8'))

		return ques_voc

	def loadAnswerVocabulary(self, answer_path=None):
		if answer_path is None:
			answer_path = self.config.ans_voc_path

		ans_voc_raw = json.load(open(answer_path, 'r'))
		ans_voc = [ w.encode('utf-8') for w in ans_voc_raw]
		return ans_voc

	#TODO: Change this to pandas dataframe! Json is DUMB!
	def loadQAPairs(self, qa_path):
		return json.loads(open(qa_path, 'r'))
		
	def loadImageFeatures(self, feature_path=None):
		return np.load(feature_path)

	def loadDataFrame(self, df_path = None):
		if df_path is None:
			df_path = self.config.df_path

		df  = pd.read_pickle(df_path)
		return df

	def getQuestionList(self, df, column_name = 'question'):
		return df[column_name]

	def loadQuestionTokenizer(self, file_path = None):
		if file_path is None:
			f = file(self.config.qtok_file_path, 'rb')
		else:
			f = file(file_path, 'rb')

		qtok = pickle.load(f)
		f.close()
		return qtok

	def getQuestionTokenizer(self, ques = None):
		qtok = text.Tokenizer(nb_words=None,filters=text.base_filter(),lower=True,split=' ');
		qtok.fit_on_texts(ques);
		return qtok

	def getAnswerTokenizer(self, ans_voc):
		atok = text.Tokenizer(nb_words=None,filters=nothing_filter(),lower=True,split='~')
		atok.fit_on_texts(ans_voc)
		return atok
	
	def calculateQuestionTokens(self, ques_list):
		ques_list_encoded = []
		for ques in  ques_list:
			ques = process_string(ques).encode('utf-8')
			ques_list_encoded.append(ques)

		question_seq = self.qtok.texts_to_sequences(ques_list_encoded)
		max_len = 20
		question_seq = sequence.pad_sequences(question_seq, maxlen=max_len)
		return question_seq

	def calculateAnswerTokens(self, ans):
		ans_seq = self.atok.texts_to_sequences(train_ans)
		return ans_seq

	def calculateImageFeatures(self, imageNameList):
		img_features = np.zeros((len(train_data_raw), 4096), dtype=np.float32)
		
		return img_features

	# Useless function. Ignore!
	def computeTrainingImageFeatures(self):
		train_ques = []
		train_ans = []
		img_feat_train = np.zeros((len(train_data_raw), 4096), dtype=np.float32)

		for i in range(len(train_data_raw)):
		    train_ques.append(train_data_raw[i][1].encode('utf-8'))
		    ans = train_data_raw[i][2]
		    if ans == '':
		        ans = 'emptystring'
		    train_ans.append(ans.encode('utf-8'))
		    img_pos = train_data_raw[i][5]
		    img_feat_train[i,:] = img_feat_train_raw[img_pos,:]

		qtok = text.Tokenizer(nb_words=None,filters=text.base_filter(),lower=True,split=' ');
		qtok.fit_on_texts(train_ques);
		q_word_idx = qtok.word_index;
		train_q_toked = qtok.texts_to_sequences(train_ques);

		val_quesid = []
		val_mc_ans = []
		val_ques = []
		val_ans = []
		img_feat_val = np.zeros((len(val_data_raw), 4096), dtype=np.float32)

		for i in range(len(val_data_raw)):
		    val_quesid.append(val_data_raw[i][0])		
		    val_ques.append(val_data_raw[i][1].encode('utf-8'))
		    mc_ans = []
		    for mc in val_data_raw[i][3]:
		        mc_ans.append(mc.encode('utf-8'))
		    val_mc_ans.append(mc_ans)
		    img_pos = val_data_raw[i][5]
		    img_feat_val[i,:] = img_feat_val_raw[img_pos,:]
		    
		val_q_toked = qtok.texts_to_sequences(val_ques);

		ans_voc = [ w.encode('utf-8') for w in ans_voc_raw]

		atok = text.Tokenizer(nb_words=None,filters=nothing_filter(),lower=True,split='~');
		atok.fit_on_texts(ans_voc);
		a_word_idx = atok.word_index;

		train_a_toked = atok.texts_to_sequences(train_ans);
		#val_a_toked = atok.texts_to_sequences(val_ans);
		train_a_toked = [c[0] for c in train_a_toked]
		#val_a_toked = [c[0] for c in val_a_toked]
		val_mc_toked = []
		for i in range(len(val_mc_ans)):
		    val_mc_toked.append(atok.texts_to_sequences(val_mc_ans[i]))


		mtr = max(len(x) for x in train_q_toked)  # maximum length of questions in train
		mte = max(len(x) for x in val_q_toked)    # maximum length of questions in val
		max_len = max(mtr,mte);

		print 'the max length of question from train and val is ' + str(max_len) + ' and doing padding...'
		train_q_toked = sequence.pad_sequences(train_q_toked, maxlen=max_len)
		val_q_toked = sequence.pad_sequences(val_q_toked, maxlen=max_len)

		print 'Building the model...'
		max_question_features = len(q_word_idx.keys())+1
		max_answer_features = len(a_word_idx.keys())


	def loadModel(self, model_path=None):
		if model_path is None:
			self.model = pickle.load(file('/srv/share/visualAttention/data/model_cloudCV.pkl', 'rb'))
		else:
			self.model = pickle.load(file(model_path, 'rb'))
		return self.model

	# TODO: Copy over Jiasen's code here.
	def train():
		pass

	# To predict the answer. Expects a question string and image feature. 
	# Calculates the question features here. 
	# TODO: Add the image feature extraction part here. Basically call Abhishek's code for a single image.
	def predict(self, question, image_features, count=None):
		if count is None:
			count = 10

		train_q_toked = self.calculateQuestionTokens([question])
		image_features = np.asarray([image_features])
		
		# model = pickle.load(file('/srv/share/visualAttention/data/model_cloudCV.pkl', 'rb'))
		a_word_idx = self.atok.word_index;

		predictions = self.model.predict([train_q_toked, image_features]);
		predicted_classes = np_utils.categorical_probas_to_classes(predictions);
		label_set = sorted(range(len(predictions[0])),key=lambda x: predictions[0][x], reverse = True)[:count]
		a_word_idx = self.atok.word_index
		a_word_rev = dict ((v,k) for k, v in a_word_idx.items())
		predictions_list = []
		for i in range(count):
		    idx = label_set[i] + 1
		    # print 'The Top %d predict Answer is : %s, with score %.6f' %(i, a_word_rev[idx], predictions[0][idx])
		    predictions_list.append((a_word_rev[idx], predictions[0][idx]))
		
		return predictions_list

	# TODO: Write batch implementation. 

