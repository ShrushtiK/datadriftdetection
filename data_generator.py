import arff, numpy as np
# dependencies: liac-arff AND NOT arff

index=0

# driftType: integer 1-4 for each type of drift 
# streamData: if True it returns stream data, otherwise it return batch
# batchSize: the batch size (only for batch data). If streamData=True, then it can be ommited (default 10)
# returns the next in order batch of data (for batch data)/next data point (for stream data)
def getData(driftType, streamData, batchSize=10):
    # find file based on type of drift
    if driftType==1:
        file="sea_tst1.arff"
    elif driftType==2:
        file="sea_tst2.arff"
    elif driftType==3:
        file="sea_tst3.arff"
    elif driftType==4:
        file="sea_tst4.arff"
    else:
        return # TODO: raise error?

    path='DriftSets/'+file
    data = arff.load(open(path, 'r'))['data']

    # transform to numpy array
    data = np.array(data)
    length=data.shape[0]

    # define how many data points will be returned
    if streamData:
        iter=1
    else:
        iter=batchSize

    results=[]
    global index
    for i in range(index, index+iter):
        results.append(data[i])
        index+=1
        
    return results

if __name__ == "__main__":
    # stream data
    stream=True
    data=getData(1, stream)
    print(data)
    data=getData(1, stream)
    print(data)

    # batch data
    stream=False
    data=getData(1, stream)
    print(data)
    data=getData(1, stream)
    print(data)
