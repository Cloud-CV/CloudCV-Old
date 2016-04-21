"""
Get annotations, rows which have been deleted.
"""
def getAnnotations(atok, hitDF):
    a_word_idx = atok.word_index
    a_word_rev = dict ((v,k) for k, v in a_word_idx.items())
    annotations= []
    deleted_rows = []
    for i, ans in enumerate(hitDF['mcqAnswer']):
        train_ans = atok.texts_to_sequences([ans.encode('utf-8')])
        train_a_token = train_ans[0]
        if train_a_token == []:
            train_a_token = ''
            deleted_rows.append(i)
        else:
            train_a_token = train_a_token[0]
        if (train_a_token == ''):
            train_a_token = '778'
        annotations.append(int(train_a_token) - 1)
        
    return annotations, deleted_rows

"""
Drop deleted_rows from Dataframe.
"""
def dropDataFrameRows(hitDF, deleted_rows):
    hitDF_pruned = hitDF.drop(hitDF.index[deleted_rows])
    return hitDF_pruned

"""
Drop data rows from input data and labels for finetuning.
"""
def dropFineTuningDataRows(mlp_input,annotations, deleted_rows):
    ann_arr = np.array(annotations)
    mlp_input_pruned = np.delete(mlp_input, deleted_rows, 0)
    mlp_input_pruned = mlp_input_pruned.astype(np.float32)
    ann_arr_pruned = np.delete(ann_arr, deleted_rows, 0)
    ann_arr_pruned = ann_arr_pruned.astype(np.float32)
    
    print mlp_input_pruned.shape
    print ann_arr_pruned.shape
    
"""
Save training data for finetuning
"""
def saveTrainingData(train_file, data, label):
    a = data.reshape(-1, 2048,1,1)
    b = label
    import h5py
    import numpy as np
    
    with h5py.File(train_file, 'w') as f:
        f['data'] = a
        f['annotations'] = b
        
"""
Save validation data for finetuning
"""
def saveValidationData(val_file, data, label):
    a = data.reshape(-1, 2048,1,1)
    b = label
    import h5py
    import numpy as np
    
    with h5py.File(val_file, 'w') as f:
        f['data'] = a
        f['annotations'] = b
        
