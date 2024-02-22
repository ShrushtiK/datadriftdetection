# consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'data_stream',
    bootstrap_servers=['broker:29092'],
    api_version=(0, 11, 5),
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     group_id='my-group',
     value_deserializer=lambda x: json.loads(x.decode('utf-8')))

for message in consumer:
    # message = message.value
    print(f"Received data: {message}")