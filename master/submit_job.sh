#!/bin/bash

/opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.master.Master &
#until nc -z localhost 7077; do
#  sleep 1
#done

# Submit the Spark job
/opt/bitnami/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12 /usr/app/gbt_model.py