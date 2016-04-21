import sys
sys.path.append('/home/harsh/caffe')
sys.path.append('/home/harsh/caffe/barrista')

import barrista
import barrista.design as design
from barrista.monitoring import ProgressIndicator

import sys
import os
sys.path.append('/var/www/html/visualAttention/database')

import cStringIO
from PIL import Image
import PIL.Image
import peewee
import numpy
import scipy
import redis
import os
import json
import base64
# from database import *
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# VQA Imports
import skimage.io as io
import random

import pandas as pd
import numpy as np
import scipy as sc

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

from barrista import solver
from barrista.monitoring import ProgressIndicator, Checkpointer, JSONLogger
import barrista.design as ds

import os
import pdb

dataDir = '/home/harsh/visualAttention/VQA'

sys.path.append('/var/www/html/visualAttention/database')
sys.path.append(dataDir)
sys.path.append(os.path.join(dataDir, 'PythonEvaluationTools/vqaEvaluation'))
sys.path.append(os.path.join(dataDir, 'PythonHelperTools/vqaTools'))
sys.path.append('/home/harsh/visualAttention/vqalib/LSTM+MLP')

from vqa import VQA
from vqaEval import VQAEval
from VQABaseline_LSTM import *
from scipy import misc
from matplotlib import pyplot as plt
import numpy as np
import h5py

class Config:
    def __init__(self, lr = 0.1):
        self.lr = lr
        self.ans_num = 1000
        self.embedding_num = 200
        self.dim_question = 1024
        self.dim_caffe = 1024
        self.batch_size = 64
        self.nb_epoch = 40
        self.nhidden1 = 1024
        self.data_path = '/srv/share/visualAttention/data/vqa_full_release_data'
        self.img_path = os.path.join(self.data_path, 'vgg_fc7_feat/')
        self.ans_voc_path = os.path.join(self.data_path, 'top_ans_'+ str(self.ans_num) +'.json')
        self.train_path = os.path.join(self.data_path, 'QAPair_'+ str(self.ans_num) +'_train2014_train.json')
        self.val_path = os.path.join(self.data_path, 'QAPair_'+ str(self.ans_num) +'_val2014_val.json')
        self.train_feat_path = self.img_path + 'train2014_fc7.npy'
        self.val_feat_path = self.img_path + 'val2014_fc7.npy'
        self.model_path = "/srv/share/visualAttention/model_cloudCV.pkl"
        self.df_path = '/srv/share/data/visualAttention.pkl'
        self.qtok_file_path = '/srv/share/visualAttention/data/vocab.pkl'
        self.model_path = "/srv/share/visualAttention/vqa_model_concat_q_i/lr_"+str(self.lr)+"_weights_"+str(self.nhidden1)+'_'+str(self.ans_num)+"_fc7.hdf5"

def nothing_filter():
    f = '';
    return f

class ConcatModel():
    def __init__(self, config):
        self.config = config
        left = Sequential()
        left.add(Embedding(12496, config.embedding_num));
        left.add(LSTM(output_dim=config.dim_question, return_sequences=False))
        
        
        right = Sequential()
        right.add(Dense(config.dim_caffe, input_dim=4096))
        right.add(Activation('tanh'))
        
        self. model = Sequential()
        self.model.add(Merge([left, right], mode='concat'))
        # self.model.add(Activation('tanh'))
        # self.model.add(Dropout(0.5))
        self.model.add(Dense(config.nhidden1))
        self.model.add(Activation('tanh'))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(1000))
        self.model.add(Activation("softmax"))
        
        keras.optimizers.RMSprop(lr=config.lr, rho=0.9, epsilon=1e-6)
        self.model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
        
        self.model.load_weights(config.model_path)
        
    def saveCaffeModelWeights(self, deploy_path, model_path):
        new_netspec = ds.NetSpecification.from_prototxt(filename=deploy_path)
        net = new_netspec.instantiate()
        net.params['fc_1'][0].data[...] = model.layers[1].get_weights()[0].T
        net.params['fc_1'][1].data[...] = model.layers[1].get_weights()[1]
        net.params['fc_2'][0].data[...] = model.layers[4].get_weights()[0].T * 0.5
        net.params['fc_2'][1].data[...] = model.layers[4].get_weights()[1]
        net.save(model_path)
        
    def getActivationsConcat(self, imageFeatures, questionFeatures):
        layer = 0
        get_activations = theano.function(self.model.layers[0].input, self.model.layers[layer].get_output(train=False), allow_input_downcast=True)
        mlp_input = get_activations(train_q_toked, imageFeatures)
        return mlp_input


class MulModel:
	def __init__(self, max_question_features, max_answer_features, config):
		print "Starting Compiling Model..."
		left = Sequential()
		left.add(Embedding(12496, config.embedding_num));
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
		self.model.add(Dense(config.nhidden1, 1000))
		self.model.add(Activation("softmax"))
		keras.optimizers.RMSprop(lr=0.00001, rho=0.9, epsilon=1e-6)
		self.model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
		print "Compilation Done."
		self.model.load_weights(config.model_path)
	
	def saveCaffeModelWeights(self, deploy_path, model_path):
        new_netspec = ds.NetSpecification.from_prototxt(filename=deploy_path)
        net = new_netspec.instantiate()
        net.params['fc_1'][0].data[...] = model.layers[1].get_weights()[0].T * 0.5
        net.params['fc_1'][1].data[...] = model.layers[1].get_weights()[1]
        net.params['fc_2'][0].data[...] = model.layers[4].get_weights()[0].T * 0.5
        net.params['fc_2'][1].data[...] = model.layers[4].get_weights()[1]
        net.save(model_path)
        
    def getActivationsConcat(self, imageFeatures, questionFeatures):
        layer = 0
        get_activations = theano.function(self.model.layers[0].input, self.model.layers[layer].get_output(train=False), allow_input_downcast=True)
        mlp_input = get_activations(train_q_toked, imageFeatures)
        return mlp_input

       
		
