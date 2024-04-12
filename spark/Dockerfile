FROM bitnami/spark:latest

WORKDIR /usr/app

COPY spark_stream.py spark_stream.py

COPY submit_job.sh submit_job.sh

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

#CMD ["/usr/app/submit_job.sh"]
CMD /opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.master.Master & /opt/bitnami/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12 /usr/app/spark_stream.py