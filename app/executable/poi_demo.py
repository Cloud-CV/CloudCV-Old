import cv2
import sys
from cv import CV_HAAR_SCALE_IMAGE
from math import sqrt
import numpy
from poi_files.svmutil import svm_load_model
from poi_files.svmutil import svm_predict
modelFolder = '/home/ubuntu/cloudcv/cloudcv17/app/executable/poi_files/'
# modelFolder = 'poi_files/'
#svmModel = svm_load_model(modelFolder+'poi_Demo.model')
svmModel = svm_load_model(modelFolder+'poi_linear.model')
minSVR = -1.4
maxSVR = 1.4

def show_faces(imagePath, modelPath):
    face_cascade = cv2.CascadeClassifier(modelPath)
    img = cv2.imread(imagePath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(0, 0), flags = CV_HAAR_SCALE_IMAGE)
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    cv2.imshow('img', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def extract_features(imagePath, model_path=modelFolder+'haarcascade_frontalface_alt.xml'):
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

def sortDebug(input_list):
    heapify(input_list, len(input_list))
    end = len(input_list) - 1
    while end > 0:
        tmp = input_list[end]
        input_list[end] = input_list[0]
        input_list[0] = tmp
        end -= 1
        siftDown(input_list, 0, end)
    return input_list


def heapify(a, count):
    start = (count-2)/2
    while start >= 0:
        siftDown(a, start, count-1)
        start -= 1


def siftDown(a, start, end):
    root = start
    while root * 2 + 1 <= end:
        child = root * 2 + 1
        swap = root
        if a[swap] > a[child]:
            swap = child
        if child+1 <= end and a[swap] > a[child+1]:
            swap = child + 1
        if swap == root:
            return
        else:
            tmp = a[root]
            a[root] = a[swap]
            a[swap] = tmp
            root = swap


def heapifyPeople(input_list, count, face_features):
    start = (count-2)/2
    while start >= 0:
        siftDownPeople(input_list, start, count-1, face_features)
        start -= 1

def siftDownPeople(a, start, end, face_features):
    root = start
    while root * 2 + 1 <= end:
        child = root * 2 + 1
        swap = root
        if performRegression(face_features[a[swap]], face_features[a[child]]):
            swap = child
        if child+1 <= end and performRegression(face_features[a[swap]], face_features[a[child+1]]):
            swap = child + 1
        if swap == root:
            return
        else:
            tmp = a[root]
            a[root] = a[swap]
            a[swap] = tmp
            root = swap

def performRegression(test_feature1, test_feature2):
    test_feature = test_feature1 - test_feature2
    (val, x, y) = svm_predict([1], [test_feature.tolist()], svmModel, '-q')
    return val[0] > 0


def rankPeople(face_features):
    numPeople = len(face_features)
    input_list = range(0, numPeople)

    heapifyPeople(input_list, numPeople, face_features)
    end = numPeople - 1
    while end > 0:
        tmp = input_list[end]
        input_list[end] = input_list[0]
        input_list[0] = tmp
        end -= 1
        siftDownPeople(input_list, 0, end, face_features)
    return input_list

def findImportantPeople(imagePath, model_path = modelFolder+'haarcascade_frontalface_alt.xml' ):
    [faces, face_features] = extract_features(imagePath, model_path)
    rank = rankPeople(numpy.array(face_features))
    ranked_faces = []
    if len(faces) != 0 and len(faces) != 1:
        for r in rank:
            ranked_faces.append(faces[r])
    # Return top 5 faces
    ranked_faces = ranked_faces[:5]
    return ranked_faces

def performLinearRegression(test_feature):
    (val, x, y) = svm_predict([1], [test_feature.tolist()], svmModel, '-q')
    return val[0]

def rankPeopleLinear(face_features):
    numPeople = len(face_features)
    input_list = range(0, numPeople)
    for i in range(0, numPeople):
        input_list[i] = performLinearRegression(face_features[i])
    return input_list

def findRelativeImportance(imagePath, model_path = modelFolder+'haarcascade_frontalface_alt.xml' ):
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
            modelPath = modelFolder+'haarcascade_frontalface_alt.xml'
        else:
            modelPath = sys.argv[2]
    imagePath = sys.argv[1]
    print findRelativeImportance(imagePath, modelPath)
    exit(0)
