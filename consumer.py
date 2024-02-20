# consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'randomNumbers',
     bootstrap_servers=['kafka:9092', '127.0.0.1:9092'],
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     group_id='my-group',
     value_deserializer=lambda x: json.loads(x.decode('utf-8')))

for message in consumer:
    message = message.value
    print(f"Received data: {message}")