import os
import sys
import time

import numpy

import theano
import theano.tensor as T
import pdb
from logistic_sgd import LogisticRegression, load_data
from MLP import HiddenLayer, MLP


def mlp_test(test_set, Model, n_input = 2030, n_output = 150, n_hidden=50):
    datasets = load_data(test_set, test_set, test_set)

    test_set_x, test_set_y = datasets[0]
    index = T.lscalar()  # index to a [mini]batch

    x = T.vector('x')  # the data is presented as rasterized images
    y = T.ivector('y')  # the labels are presented as 1D vector of

    rng = numpy.random.RandomState(1234)
    # construct the MLP class
    classifier = MLP(
        rng=rng,
        input=x,
        n_in=n_input,
        n_hidden=n_hidden,
        n_out=n_output,
        Model = Model
    )

    #classifier.hiddenLayer.__setstate__((Model['hidden_W'], Model['hidden_b']))
    #classifier.logRegressionLayer.__setstate__((Model['logRegression_W'], Model['logRegression_b']))

    test_model = theano.function(
        inputs=[index],
        outputs=classifier.predictAll,
        givens={
            x: test_set_x[index],
        }
    )

    out = test_model(0).tolist()

    return out