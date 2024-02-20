# producer.py
from kafka import KafkaProducer
import time
import json
import random

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
                        api_version=(0, 11, 5),
                         value_serializer=lambda x:
                         json.dumps(x).encode('utf-8'))

while True:
    data = {'number': random.random()}
    producer.send('data_stream', data)
    print(f"Sent data: {data}")
    time.sleep(1)