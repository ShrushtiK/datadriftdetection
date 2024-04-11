# ECiDA: Data and Concept Drift Detection

## Introduction 
In the dynamic field of machine learning, even the most exceptional models encounter hidden risks known as data and concept drift. Data drift refers to a change in the statistical properties of data, rendering predictions outdated. Concept drift indicates a fundamental shift over time in the relationship between the input and the target.

This project is in collaboration with the ECiDA platform (Evolutionary Changes in Data Analysis). Our main aim is to uncover the aforementioned risks by using a distributed monitoring solution. We focus on data drift detection. After training a machine learning model using historical data, we then continuously analyze data streams to detect statistical deviations. This proactive approach enables timely responses, such as retraining models and adjusting data pipelines, ensuring that machine learning models remain accurate and effective in a constantly evolving world.

## Implementation
### Architecture
A diagram of the project's architecture can be found within the repository in the form of a PDF. It can be accessed [here]("Scalable Computing Project Architecture.pdf").

We chose to use a real-world dataset, as described in (Street and Kim, 2001). The dataset can be found [here](https://www.win.tue.nl/~mpechen/data/DriftSets/).

### Infrastructure
Managed to have our components aka Spark, Kafka, Cassandra and Data Generator up via docker compose and succesfully able to update Cassandra with our dataset values via a Spark job

### UI, Historical & Streaming Data

### Core Algorithm & Data location awareness
In this section, we provide answers to the following questions: 
- How is the data distributed? 
- Why is the choice made for this particular dataset? 
- What is the partitioning schema? 
- If you are using full data replication , then why is this choice made? 
- Are you processing data that are located on the same node? If not, why?
- How can you prove data location awareness in your project?

### Scalability & Fault tolerance
In this section, we provide answers to the following questions: 
- What will happen if one of the nodes goes down? 
- What is happening on the level of data distribution? 
- What are the limits of your implementation and how can those be addressed? (CPU, RAM, I/O etc.)

## Results
e.g. single machine vs multi-machine cluster

## References
W. Street, Y. Kim, **A streaming ensemble algorithm (SEA) for large- scale classification**, in: KDD'01, 7th International Conference on Knowledge Discovery and Data Mining, San Francisco, CA, August 2001, pp. 377-382.


## Existing notes (delete when done!):
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

setup_spark.sh:

Install and configure Spark, it downloads the custum Spark docker image from DockerHub
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