#!/bin/bash

export MASTER=spark://spark-master:7077
export SPARK_WORKER_INSTANCES=2
export CORES_PER_WORKER=1
export TOTAL_CORES=$((${CORES_PER_WORKER}*${SPARK_WORKER_INSTANCES}))
export TFoS_HOME=/.local/lib/python3.11/site-packages/tensorflowonspark

${SPARK_HOME}/sbin/start-master.sh; ${SPARK_HOME}/sbin/start-worker.sh -c $CORES_PER_WORKER -m 3G ${MASTER}

# remove any old artifacts
rm -rf ${TFoS_HOME}/mnist_model
rm -rf ${TFoS_HOME}/mnist_export

# train and validate
${SPARK_HOME}/bin/spark-submit \
--master ${MASTER} \
--conf spark.cores.max=${TOTAL_CORES} \
--conf spark.task.cpus=${CORES_PER_WORKER} \
${TFoS_HOME}/examples/mnist/estimator/mnist_tf.py \
--cluster_size ${SPARK_WORKER_INSTANCES} \
--model_dir ${TFoS_HOME}/mnist_model \
--export_dir ${TFoS_HOME}/mnist_export

# confirm model
ls -lR ${TFoS_HOME}/mnist_model
ls -lR ${TFoS_HOME}/mnist_export

