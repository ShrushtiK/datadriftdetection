#!/bin/bash

helm install spark bitnami/spark
helm upgrade spark bitnami/spark --set worker.replicaCount=1 --set worker.coreLimit=1 --set worker.memoryLimit=256m --set image.repository=sarahema/spark-scalable --set image.tag=1.2.0
export PYTHON_SCRIPT_PATH="/usr/app/spark_stream.py"
kubectl exec -ti --namespace default spark-worker-0 -- spark-submit --master spark://spark-master-svc:7077 --py-files $PYTHON_SCRIPT_PATH --files $PYTHON_SCRIPT_PATH --name SparkStreamingJob $PYTHON_SCRIPT_PATH