# producer.py
from kafka import KafkaProducer
import time
import json
import random

producer = KafkaProducer(bootstrap_servers=['kafka:9092', '127.0.0.1:9092'],
                         value_serializer=lambda x:
                         json.dumps(x).encode('utf-8'))

while True:
    data = {'number': random.random()}
    producer.send('randomNumbers', value=data)
    print(f"Sent data: {data}")
    time.sleep(1)