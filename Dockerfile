FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y netcat-openbsd

RUN pip install kafka-python==2.0.2 numpy liac-arff

COPY . /app

WORKDIR /app

# Wait for Kafka to be ready before creating the topic
CMD ["sh", "-c", "while ! nc -z broker 9092; do sleep 1; done && confluent local kafka topic create data-stream"]

