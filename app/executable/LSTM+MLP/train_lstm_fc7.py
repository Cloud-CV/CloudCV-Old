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

import pdb
def nothing_filter():
	f = '';
	return f

if __name__ == '__main__':

	sys.setrecursionlimit(10000)
	ans_num = 1000
	embedding_num = 200
	dim_question = 1024
	dim_caffe = 1024
	batch_size = 64
	nb_epoch = 20
	nhidden1 = 1024

	img_path = '../data/vgg_fc7_feat/'

	load_model = True
	model_path = "cv/weights_"+str(nhidden1)+'_'+str(ans_num)+"_fc7.hdf5"

	ans_voc_path = '../data/Old/LSTM/top_ans_'+ str(ans_num) +'.json'
	print 'reading %s...' %(ans_voc_path)
	ans_voc_raw = json.load(open(ans_voc_path, 'r'))

	train_path = '../data/Old/LSTM/QAPair_'+ str(ans_num) +'_train2014_train.json'
	val_path = '../data/Old/LSTM/QAPair_'+ str(ans_num) +'_val2014_val.json'

	# load train and val encoding data
	print 'reading %s...' %(train_path)
	train_data_raw = json.load(open(train_path, 'r'))	
	print 'reading %s...' %(val_path)
	val_data_raw = json.load(open(val_path, 'r'))


	train_feat_path = img_path + 'train2014_fc7.npy'
	print 'Loading image path: ' + train_feat_path
	img_feat_train_raw = np.load(train_feat_path)

	val_feat_path = img_path + 'val2014_fc7.npy'
	print 'Loading image path: ' + val_feat_path
	img_feat_val_raw = np.load(val_feat_path)


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
	train_q_toked = qtok.texts_to_sequences(train_ques);
	q_word_idx = qtok.word_index;
	
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

		img_feat_val[i,:] = img_feat_val_raw[val_data_raw[i][5],:]
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


	mtr = max(len(x) for x in train_q_toked)
	mte = max(len(x) for x in val_q_toked)
	max_len = max(mtr,mte);
	
	print 'the max length of question from train and val is ' + str(max_len) + ' and doing padding...'
	train_q_toked = sequence.pad_sequences(train_q_toked, maxlen=max_len)
	val_q_toked = sequence.pad_sequences(val_q_toked, maxlen=max_len)
	print 'Building the model...'
	max_question_features = len(q_word_idx.keys())+1
	max_answer_features = len(a_word_idx.keys())

	left = Sequential()
	left.add(Embedding(max_question_features,embedding_num));
	left.add(LSTM(embedding_num,dim_question)) #, return_sequences=True))

	right = Sequential()
	right.add(Dense(4096, dim_caffe))
	right.add(Activation('tanh'))

	model = Sequential()
	model.add(Merge([left, right], mode='mul'))
	model.add(Activation('tanh'))
	model.add(Dropout(0.5))
	model.add(Dense(dim_question, nhidden1))
	model.add(Activation('tanh'))
	model.add(Dropout(0.5))	
	model.add(Dense(nhidden1, max_answer_features))
	model.add(Activation("softmax"))
	keras.optimizers.RMSprop(lr=0.00001, rho=0.9, epsilon=1e-6)
	model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

	print 'Getting the Question and answer feat for image'

	train_q_toked = np.asarray(train_q_toked)
	train_a_toked = np.asarray(train_a_toked);

	val_q_toked = np.asarray(val_q_toked)
	#val_a_toked = np.asarray(val_a_toked);

	train_a_toked = np_utils.to_categorical(train_a_toked, max_answer_features+1)
	train_a_toked = train_a_toked[:,1:]	
	#val_a_toked = np_utils.to_categorical(val_a_toked, max_answer_features+1)
	
	checkpointer = ModelCheckpoint(filepath=model_path, verbose=1, save_best_only=True)
	if load_model:
		print 'Loading Model from :' + model_path
		model.load_weights(model_path)

		model.fit([train_q_toked, img_feat_train], train_a_toked, batch_size=32, nb_epoch=nb_epoch, 
			validation_split = 0.1, show_accuracy=True, callbacks=[checkpointer])

	predictions = model.predict([val_q_toked, img_feat_val],batch_size=batch_size);
	predicted_classes = np_utils.categorical_probas_to_classes(predictions);
	MC_prediction_classes = []
	for i in range(len(predictions)):
		mc_prob = []
		mc_index = []
		for j in range(len(val_mc_toked[i])):
			if val_mc_toked[i][j] != []:
				index = val_mc_toked[i][j][0]-1
				mc_index.append(index)
				mc_prob.append(predictions[i][index])

		MC_prediction_classes.append(mc_index[np.argmax(mc_prob)])

	a_word_rev = dict ((v,k) for k, v in a_word_idx.items())
#	print 'Converting back to words.'	
#	rq, ra, rp = idx_to_words(val_q_toked, predicted_classes, q_word_idx, a_word_idx)
	
	answer_store = []
	for i in range(len(val_quesid)):
		idx = predicted_classes[i] + 1
		answer_store.append({'question_id': val_quesid[i], 'answer':a_word_rev[idx]})
	
	answer_save_path = "cv/result_"+str(nhidden1)+'_'+str(ans_num)+"fc7.json"

	with open(answer_save_path, 'w') as data_file:
		json.dump(answer_store, data_file)

	MC_answer_store = []
	for i in range(len(val_quesid)):
		MC_answer_store.append({'question_id': val_quesid[i], 'answer':a_word_rev[MC_prediction_classes[i]+1]})
	
	answer_save_path = "cv/MC_result_"+str(nhidden1)+'_'+str(ans_num)+"fc7.json"

	with open(answer_save_path, 'w') as data_file:
		json.dump(MC_answer_store, data_file)
