# DataAndConceptDriftDetection



## Deadline 1 - Architecture
Uploaded the architecture of the project in "Scalable Computing Project Architecture.pdf"

## Deadline 2 - Infrastructure
Managed to have our components aka Spark, Kafka, Cassandra and Data Generator up via docker compose and succesfully able to update Cassandra with our dataset values via a Spark job

## Deadline 3 
Created Spark job for training and testing a GBTRegressor on the dataset and check for potential drift by seeing the biggest drops in prediction accuracies. But, the event is manually triggered by "exec"-ing into the spark-master. Without the support of an event-based architecture, it seems very hard to have a functional and automated pipeline for the project. For instance
- triggering the training job once we have "enough historical data" in the database
- trigger testing once the model is prepared
- re-train the model again once the drift is detected for too long
- how to differentiate the data that the model trains on versus the once it predicts detection on (the data used for testing must also become a part of the training set once the model is being re-trained), and so on. 
For now, the testing has been done via the following   
```
docker compose up --build --scale spark-worker=4
```

## Deadline 4
- Integration of Grafana and connectivity with Cassandra
- Integration of Airflow for Spark jobs (training and testing)
- Cassandra table redesign for storing historical data and saving predictions + Cassandra partitioning (full replication)

## Deadline 5-6:
- Deployed Airflow on Kube
- Deployed Spark on Kube
- Deployed Kafka  on Kube
- Deployed CassandraDB  on Kube
- Deployed Kafka Producer  on Kube
- Submit the data stream job on Spark  on Kube
- Connected Spark with Kafka, creation of data stream and dataframe  on Kube
- Connecting Spark with CassandraDB: still needs to solve autentication problem with CassandraDB  on Kube


Data location awareness.
For this deadline we expect you to implement the algorithm(s) of your choice, in a
scalable fashion such that they can be executed on your pipeline. Use the data
sets that you obtained from the previous deadline. You should have, at the very
least, a basic version of your algorithm running and demonstrate it during the
computer labs. Also think about the next deadline. The very important principal
questions for this deadline are:
○ How is your data distributed?
○ Why is the choice made for this particular dataset?
○ What is the partitioning schema?
○ If you are using full data replication , then why is this choice made?
○ Are you processing data that are located on the same node? If not, why?
○ How can you prove data location awareness in your project?

Dataset: Synthetic data for data and concept drift. 
Spark RDD vs Dataframe - we use Dataframes: RDDs are immutable and distributed collections of data stored on the spark workers. Dataframes are higher-level abstractions of RDDs which are organized into tables of columns. The MLSpark library also defaults to using Dataframes.
Fault-tolerance: When a worker node fails, the DAGs (transformations of data) applied on the local RDDs of the worker are saved so that they can be recomputed when the new worker spawns and resumes the DAG tasks of the previous worker.
![images/lineage.png](images/lineage.png)
Data Locality Awareness: The key-value RDDs have their keys hashed so that the Spark context is aware of the location of each RDD after the partitioning of the data into RDDs and the distribution of the RDDs to the different workers. Data locality has different levels in Spark, which is configurable, but we kept the default level. The different levels of data locality in Spark are:
1. NO_PREF: no locality preference; it starts from PROCESS_LOCAL and changes to higher levels by necessity
2. PROCESS_LOCAL: process RDDs from the same JVM
3. NODE_LOCAL: process RDDs from the same spark node, possibly from different executors from the same node. Adds network latency because data needs to travel
4. RACK_LOCAL: process RDDs from the same rack, but different servers.
5. ANY: process RDDs from another network altogether

In out case, setting the data locality to NO_PREF means that Spark will schedule to process on the same executor the data stream stored in the Dataframes on Spark and going out to Cassandra. Since we use the setting `spark.locality.wait(default value is 3s)`, the Spark manager will wait 3 seconds of unresponsiveness from the worker (if the worker is stuck in one data transformation and delays the next data point incoming) until it will redirect the load of the RDDs partition to another executor on the same node (PROCESS_LOCAL). If the whole worker node runs out of hardware resources, then the RDDs will be redirected to another worker node (NODE_LOCAL). 

![images/data_locality.png](images/data_locality.png)
Data Partitioning: The RDDs are built based on a partition schema for the data. Since we are using a Dataframe, the partitioning schema is based on a column of the table. We chose te column 'label', which takes binary values 0 and 1, as the partitioning schema column, because this will enforce a minimum of two RDDs for the data, scalable to subsets of RDD(0) and RDD(1) if the Spark manager redistributes the workload to other executors. The column 'label' was chosen because the other columns have unique values, which would lead to many inefficient RDD partitions. How this will work in our ML setup jobs is:
- One executor will get the data with the RDDs formed out of  the rows in Cassandra with the 'label' value 0, and the other executor will get the partitioning with the 'label' value 1.
- The workers calculate the gradients based on their specific RDD partition, and then return the calculated gradient at the end of each parallel epoch to the master.
- The model on the master node will be updated in parallel by each worker's gradient, by data containing both label = 1 and label = 0.


setup_spark.sh:

Install and configure Spark, it downloads the custom Spark docker image from DockerHub
```
helm install spark bitnami/spark

helm upgrade spark bitnami/spark --set worker.replicaCount=1 --set worker.coreLimit=1 --set worker.memoryLimit=256m --set image.repository=sarahema/spark-scalable --set image.tag=2.10.0
```
To submit the job on Spark: first, enter the spark worker pod and send the command to the spark master service with the dependencies of the job and the job file

```
kubectl exec -ti --namespace default spark-worker-0 -- spark-submit --master spark://spark-master-svc:7077 --py-files /usr/app/spark_stream.py --name SparkStreamingJob --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12 --conf spark.cassandra.auth.username=cassandra --conf spark.cassandra.auth.password=cassandra --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp"  /usr/app/spark_stream.py  
```

spark_stream.py job:

configure cassandra cluster with authentication credentials

```
def create_cassandra_connection():
    try:
        # Connecting to the Cassandra cluster
        auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')

        cluster = Cluster(['default-cassandra.default.svc.cluster.local'], auth_provider=auth_provider)

        # Creating a session
        cas_session = cluster.connect()

        return cas_session
    except Exception as e:
        logging.error(f"Could not create Cassandra connection due to {e}")
        return None
```

specify the spark connector credentials when conencting to cassandra
```      
def create_spark_connection():
    s_conn = None
    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config("spark.executor.instances", "2") \
            .config("spark.kubernetes.container.image", "sarahema/spark-scalable:2.10.0") \
            .config("spark.kubernetes.namespace", "default") \
            .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
            .config("spark.cassandra.connection.host", "default-cassandra.default.svc.cluster.local") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.cassandra.auth.username", "cassandra") \
            .config("spark.cassandra.auth.password", "cassandra") \
            .config("spark.dynamicAllocation.enabled", "true") \
            .config("spark.dynamicAllocation.minExecutors", "1") \
            .config("spark.dynamicAllocation.maxExecutors", "2") \
            .getOrCreate()
```

setup_cassandra.sh:

# this will give it a random password
helm install default oci://registry-1.docker.io/bitnamicharts/cassandra

# here you setup the password
helm install default \
    --set dbUser.user=cassandra,dbUser.password=cassandra \
    oci://registry-1.docker.io/bitnamicharts/cassandra


# connect to the cassandra client pod with the correct auth password
kubectl run --namespace default default-cassandra-client --rm --tty -i --restart='Never'  --env CASSANDRA_PASSWORD=cassandra  --image docker.io/bitnami/cassandra:4.1.4-debian-12-r4 -- bash 

# here the script fails although this is identical to the official documentation: connect to cassandra query language after you entered the cassandra pod
cqlsh -u cassandra -p cassandra default-cassandra 9042 