# producer.py
from kafka import KafkaProducer
import time
import json
import random
import uuid

producer = KafkaProducer(
    bootstrap_servers=['broker:29092'],
                        max_block_ms=5000,
                        api_version=(0, 11, 5),
                         value_serializer=lambda x:
                         json.dumps(x).encode('utf-8'))

while True:
    unique_id = str(uuid.uuid4())
    # Create data containing the number and ID
    data = {'id': unique_id, 'number': random.random()}
    producer.send('data_stream', data)
    print(f"Sent data: {data}")
    producer.flush()
    time.sleep(1)