import sys
import os
sys.path.insert(0, '/home/jiasenlu/code/vqalib/VQA_evaluate/PythonEvaluationTools/')
import pdb
from vqaEvalDemo import evaluate

path = os.getcwd()

result_path = '/cv/most_common15'

filePath = path + result_path + '.json'

print 'Loading ' +filePath

vqaEval = evaluate(filePath)

# saving to txt

f = open(path+result_path+'_accuracy.txt', 'w')
result = "Overall Accuracy is: %.02f\n" %(vqaEval.accuracy['overall'])
f.write(result+'\n')
for quesType in vqaEval.accuracy['perQuestionType']:
	result = "%s : %.02f" %(quesType, vqaEval.accuracy['perQuestionType'][quesType])
	f.write(result+'\n')
for ansType in vqaEval.accuracy['perAnswerType']:
	result =  "%s : %.02f" %(ansType, vqaEval.accuracy['perAnswerType'][ansType])
	f.write(result+'\n')

f.close()