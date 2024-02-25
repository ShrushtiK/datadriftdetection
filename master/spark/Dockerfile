FROM bitnami/spark:latest

WORKDIR /usr/app
#RUN apt-get update
#    apt-get install python-pip

COPY . .
RUN pip3 install -r requirements.txt

CMD ["/opt/bitnami/spark/bin/spark-class", "org.apache.spark.deploy.worker.Worker", "spark://spark-master:7077"]

