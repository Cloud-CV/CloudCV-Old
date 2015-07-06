import cv2
import sys
from cv import CV_HAAR_SCALE_IMAGE
from math import sqrt
import numpy
from poi_files.svmutil import svm_load_model
from poi_files.svmutil import svm_predict
import os
modelFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poi_files')
# modelFolder = 'poi_files/'
#svmModel = svm_load_model(modelFolder+'poi_Demo.model')
svmModel = svm_load_model(modelFolder+'/poi_linear.model')
minSVR = -1.4
maxSVR = 1.4

import redis, json
redis_obj = redis.StrictRedis(host='redis', port=6379, db=0)

def log_to_terminal(message, socketid):
    redis_obj.publish('chat', json.dumps({'message': str(message), 'socketid': str(socketid)}))

def extract_features(imagePath, model_path=modelFolder+'/haarcascade_frontalface_alt.xml'):
    # Do all file checks here
    img = cv2.imread(imagePath, cv2.CV_LOAD_IMAGE_GRAYSCALE)
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    edge_im = numpy.sqrt(numpy.square(sobelx) + numpy.square(sobely))

    imheight = float(len(img))
    imwidth = float(len(img[0]))


    face_cascade = cv2.CascadeClassifier(model_path)
    faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=2, minSize=(0, 0), flags = CV_HAAR_SCALE_IMAGE)
    total_gradient = 0
    face_features = []
    numFaces = len(faces)
    scaled_faces = []

    for face in faces:
        (faceX, faceY, faceW, faceH) = face
        faceX = float(faceX)
        faceY = float(faceY)
        faceW = float(faceW)
        faceH = float(faceH)

        x = faceX / imwidth
        y = faceY / imheight
        w = faceW / imwidth
        h = faceH / imheight

        wickedDistance = sqrt((x-0.5)**2 + (y-0.5)**2)/ max(w,h)
        scale = faceW * faceH / (imwidth * imheight)
        roi = edge_im[faceY:faceY+faceH, faceX:faceX+faceW]
        sharpness = sum(sum(roi))
        face_features.append([wickedDistance, scale, sharpness])
        total_gradient = total_gradient + sharpness
        scaled_faces.append([x, y, w, h])

    for i in range(0, numFaces):
        face_features[i][2] = face_features[i][2] / total_gradient

    return scaled_faces, face_features

def performLinearRegression(test_feature):
    (val, x, y) = svm_predict([1], [test_feature.tolist()], svmModel, '-q')
    return val[0]

def rankPeopleLinear(face_features):
    numPeople = len(face_features)
    input_list = range(0, numPeople)
    for i in range(0, numPeople):
        input_list[i] = performLinearRegression(face_features[i])
    return input_list

def findRelativeImportance(imagePath, socketid, model_path = modelFolder+'/haarcascade_frontalface_alt.xml' ):
    [faces, face_features] = extract_features(imagePath, model_path)
    scores = rankPeopleLinear(numpy.array(face_features))
    normScores = []
    for x in scores:
        x = round((x-minSVR)/maxSVR, 2)*100
        if x < 0:
            x = 0.0
        if x > 100:
            x = 100.0
        normScores.append(x)
    sorted_tuple = sorted(enumerate(normScores), key=lambda x:x[1], reverse=True)
    ranked_faces = []
    for r in sorted_tuple:
        faces[r[0]].append(r[1])
        ranked_faces.append(faces[r[0]])
    # Return top 5 faces
    ranked_faces = ranked_faces[:5]
    return ranked_faces

if __name__ == '__main__':
    print "Standalone Program"
    if (len(sys.argv) <= 1):
        print "Arguments required"
        exit(1)
    else:
        if (len(sys.argv) == 2):
            modelPath = modelFolder+'/haarcascade_frontalface_alt.xml'
        else:
            modelPath = sys.argv[2]
    imagePath = sys.argv[1]
    print findRelativeImportance(imagePath, modelPath)
    exit(0)
