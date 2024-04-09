#!/bin/bash

helm install spark bitnami/spark
#helm upgrade spark bitnami/spark --set worker.replicaCount=1 --set worker.coreLimit=1 --set worker.memoryLimit=256m --set image.repository=sarahema/spark-scalable --set image.tag=3.3.0

helm upgrade spark bitnami/spark --set master.resourcesPreset=2xlarge --set worker.resourcesPreset=2xlarge --set image.repository=sarahema/spark-scalable --set image.tag=3.3.0

export PYTHON_SCRIPT_PATH="/usr/app/spark_stream.py"
kubectl exec -ti --namespace default spark-worker-0 -- spark-submit --master spark://spark-master-svc:7077 --py-files /usr/app/spark_stream.py --name SparkStreamingJob --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12 --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp"  /usr/app/spark_stream.py