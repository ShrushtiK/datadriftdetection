# producer.py
from kafka import KafkaProducer
import time
import json
import random
import uuid
# CHANGE 3
import arff, numpy as np

# CHANGE 1
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


producer = KafkaProducer(
    bootstrap_servers=['broker:29092'],
                        max_block_ms=5000,
                        api_version=(0, 11, 5),
                         value_serializer=lambda x:
                         json.dumps(x).encode('utf-8'))

while True:
    # CHANGE 2: we send the data as a whole to make the approach more dynamic
    # TODO: (drift type 1, stream data. How will the user give this input?)
    data = {'data_point': getData(1, True)} 
    producer.send('data_stream', data)
    print(f"Sent data: {data}")
    producer.flush()
    time.sleep(1)