FROM python:3.8-slim

# Install dependencies and utilities
RUN apt-get update && \
    apt-get install -y netcat-openbsd
# Copy the Python script and other necessary files
COPY . /app

WORKDIR /app

# Wait for Kafka to be ready before creating the topic
CMD ["sh", "-c", "while ! nc -z broker 9092; do sleep 1; done && confluent local kafka topic create data-stream"]
