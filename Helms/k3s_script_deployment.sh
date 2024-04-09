#!/bin/bash

# if the KUBECONFIG CLUSTER is not set to k3s.yaml, then use --kubeconfig k3s.yaml as flag in all the commands
#helm install --kube-insecure-skip-tls-verify spark bitnami/spark

helm install --kube-insecure-skip-tls-verify  spark bitnami/spark --set master.resourcesPreset=medium --set worker.resourcesPreset=medium --set spark.shuffle.service.enabled=true --set spark.dynamicAllocation.enabled=true --set image.repository=sarahema/spark-scalable --set image.tag=3.6.0

kubectl --insecure-skip-tls-verify apply -f Helms/charts/cassandra/manifests/cassandra-service.yaml
kubectl --insecure-skip-tls-verify apply -f Helms/charts/cassandra/manifests/cassandra-statefulset.yaml
kubectl --insecure-skip-tls-verify apply -f Helms/charts/kafka/zookeeper-manifest.yaml
kubectl --insecure-skip-tls-verify apply -f Helms/charts/kafka/producer-manifest.yaml
kubectl --insecure-skip-tls-verify apply -f Helms/charts/kafka/broker-manifest.yaml

kubectl --insecure-skip-tls-verify exec -it --namespace default spark-worker-0 -- spark-submit --master spark://spark-master-svc:7077 --py-files /usr/app/spark_stream.py --name SparkStreamingJob --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12 --conf spark.cassandra.auth.username=cassandra --conf spark.cassandra.auth.password=cassandra  --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp"  /usr/app/spark_stream.py