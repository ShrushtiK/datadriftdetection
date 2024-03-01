#!/bin/bash

/opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.master.Master &
export SPARK_HOME=/opt/bitnami/spark
export MASTER=spark://spark-master:7077
export SPARK_WORKER_INSTANCES=2
export CORES_PER_WORKER=1
export TOTAL_CORES=$((${CORES_PER_WORKER}*${SPARK_WORKER_INSTANCES}))

# start spark cluster
${SPARK_HOME}/sbin/start-master.sh; ${SPARK_HOME}/sbin/start-worker.sh -c $CORES_PER_WORKER -m 3G ${MASTER}


#/opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.master.Master &
#until nc -z localhost 7077; do
#  sleep 1
#done

# Submit the Spark job
#/opt/bitnami/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12 /usr/app/spark_stream.py

# train and evaluate
${SPARK_HOME}/bin/spark-submit \
--master ${MASTER} \
--conf spark.cores.max=${TOTAL_CORES} \
--conf spark.task.cpus=${CORES_PER_WORKER} \
--py-files data_setup.py \
#--cluster_size ${SPARK_WORKER_INSTANCES}
#/usr/app/model_mnist.py \
# shutdown spark
${SPARK_HOME}/sbin/stop-worker.sh; ${SPARK_HOME}/sbin/stop-master.sh

