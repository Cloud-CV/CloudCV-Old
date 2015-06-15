import time
import numpy as np

import pdb


class LinearSVM():

    def __init__(self):
        self.lin_clf = svm.LinearSVC(C=0.1)
    
    def train(self, data, label):
        self.lin_clf.fit(data, label)

    def predict(self, samples):
        return self.lin_clf.predict(samples)


class SVM():
    def __init__(self, C_val):
        self.clf = svm.SVC(C=C_val, kernel='linear',probability = 1)
    
    def train(self, data, label):

        self.model = self.clf.fit(data, label)

    def predict(self, data):
        return self.model.predict(data)

    def predictProb(self, data):
        return self.model.predict_proba(data)
def kmeans(data, k):
    # doing k means on data and return the label and k center.
    print 'Using the scikit-learn K-means clustering and returning %d centers' %(k)

    kmeans = KMeans(init='k-means++', n_clusters=k, max_iter=1000, n_init = 20)
    kmeans.fit(data)
    dis = euclidean_distances(kmeans.cluster_centers_, data)
    # find the nearset vector in data for each cluster_centers.
    ind = np.argmin(dis, axis=1)
    return kmeans.labels_, kmeans.cluster_centers_, data[np.argmin(dis, axis=1)]


