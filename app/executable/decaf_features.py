import sys
import os
os.environ['OMP_NUM_THREADS'] = '4'

def decaf_features(ImagePath):
    try:

        sys.path.append("/share/code/caffe/python")

        from caffe import imagenet
	import numpy

        # Set the right path to your model file, pretrained model,
        # and the image you would like to classify.
        MODEL_FILE = '/share/code/caffe/examples_old/imagenet_deploy.prototxt'
        PRETRAINED = '/share/code/caffe/models/caffe_reference_imagenet_model'
        IMAGE_FILE = ImagePath
        net = imagenet.ImageNetClassifier(MODEL_FILE, PRETRAINED)
        net.caffenet.set_phase_test()
        net.caffenet.set_mode_cpu()

        # Compute the features
        net.predict(IMAGE_FILE)
        blobs = net.caffenet.blobs()
        features = blobs[-3].data[:]
        print features.shape
        print features[1].shape, features[1]
        features = numpy.resize(features, (10,4096))
        print features.shape, features[1].shape
        return features
    except Exception as e:
        raise e

if __name__ == "__main__":
    print sys.argv[1]
    decaf_features(sys.argv[1])
