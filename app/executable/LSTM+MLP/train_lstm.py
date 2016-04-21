import numpy as np
import theano
import json
import cPickle as pickle
import random
import sys
np.random.seed(1234)

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

def idx_to_words(questions, answers, predictions, q_word_idx, a_word_idx, sample = 0.1):
	question_words = []
	answer_words = []
	prediction_words = []

	q_word_rev = dict ((v,k) for k, v in q_word_idx.items())
	a_word_rev = dict ((v,k) for k, v in a_word_idx.items())

	for i in range(len(questions)):
		this_q = questions[i]
		this_p = predictions[i]
		this_q_words = [q_word_rev[int(w)] for w in this_q if w in q_word_rev.keys()]
		this_q_words = ' '.join(this_q_words)
		this_p_words = a_word_rev[this_p]
		question_words.append(this_q_words)
		answer_words.append(answers[i])
		prediction_words.append(this_p_words)

	return question_words, answer_words, prediction_words


def MC_prediction():
	pass
if __name__ == '__main__':

	sys.setrecursionlimit(10000)
	ans_num = 1000
	hidden_num = 1024
	embedding_num = 200
	batch_size = 64
	nb_epoch = 40
	validate_ratio = 0.1
	print(hidden_num)
	load_model = True
	model_path = "cv/weights_"+str(hidden_num)+'_'+str(ans_num)+".hdf5"

	ans_voc_path = '../data/LSTM/top_ans_'+ str(ans_num) +'.json'
	print 'reading %s...' %(ans_voc_path)
	ans_voc_raw = json.load(open(ans_voc_path, 'r'))

	train_path = '../data/LSTM/QAPair_'+ str(ans_num) +'_train_val.json'
	val_path = '../data/LSTM/QAPair_'+ str(ans_num) +'_test2015.json'

	# load train and val encoding data
	print 'reading %s...' %(train_path)
	train_data_raw = json.load(open(train_path, 'r'))	
	print 'reading %s...' %(val_path)
	val_data_raw = json.load(open(val_path, 'r'))

	train_ques = []
	train_ans = []

	for i in range(len(train_data_raw)):
		train_ques.append(train_data_raw[i][2].encode('utf-8'))
		ans = train_data_raw[i][3]
		train_ans.append(ans.encode('utf-8'))
	
	qtok = text.Tokenizer(nb_words=None,filters=text.base_filter(),lower=True,split=' ');
	qtok.fit_on_texts(train_ques);
	train_q_toked = qtok.texts_to_sequences(train_ques);
	q_word_idx = qtok.word_index;

	val_ques = []
	val_ans = []
	val_quesid = []
	val_mc_ans = []

	for i in range(len(val_data_raw)):
		val_quesid.append(val_data_raw[i][1])
		val_ques.append(val_data_raw[i][2].encode('utf-8'))
		
		mc_ans = []
		for mc in val_data_raw[i][3]:
			mc_ans.append(mc.encode('utf-8'))
		val_mc_ans.append(mc_ans)
		
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
	max_question_features = len(q_word_idx.keys())
	max_answer_features = len(a_word_idx.keys())

	model = Sequential()
	model.add(Embedding(max_question_features+1, embedding_num))
	model.add(LSTM(embedding_num, hidden_num))
	model.add(Dropout(0.5))
	model.add(Dense(hidden_num, max_answer_features))
	model.add(Activation('softmax'))
	model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
	
	#print 'Getting the Question and answer feat for image'

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
	else:
		model.fit(train_q_toked, train_a_toked, batch_size=batch_size, nb_epoch=nb_epoch, 
				validation_split=validate_ratio, show_accuracy=True, callbacks=[checkpointer])

	predictions = model.predict(val_q_toked,batch_size=batch_size);
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
#	rq, ra, rp = idx_to_words(val_q_toked, val_ans, predicted_classes, q_word_idx, a_word_idx)
	
	answer_store = []
	for i in range(len(val_quesid)): 
		idx = predicted_classes[i] + 1
		answer_store.append({'question_id': val_quesid[i], 'answer':a_word_rev[idx]})
	
	answer_save_path = "cv/result_"+str(hidden_num)+'_'+str(ans_num)+".json"

	with open(answer_save_path, 'w') as data_file:
		json.dump(answer_store, data_file)

	MC_answer_store = []
	for i in range(len(val_quesid)):
		MC_answer_store.append({'question_id': val_quesid[i], 'answer':a_word_rev[MC_prediction_classes[i]+1]})

	answer_save_path = "cv/MC_result_"+str(hidden_num)+'_'+str(ans_num)+".json"

	with open(answer_save_path, 'w') as data_file:
		json.dump(MC_answer_store, data_file)

