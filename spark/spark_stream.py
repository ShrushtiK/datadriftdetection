import logging
import datetime
import traceback
import os
import json

from cassandra.cluster import Cluster
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, monotonically_increasing_id, row_number, expr
from pyspark.sql.types import *
from pyspark.sql.window import Window
from cassandra.auth import PlainTextAuthProvider


def create_table(session):
    session.execute("""
            CREATE KEYSPACE IF NOT EXISTS spark_streams WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
            """)
    session.execute("""
            USE spark_streams
            """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS spark_streams.drift_analysis (
            test_timestamp TIMESTAMP,
            id UUID,
            label FLOAT,
            prediction FLOAT,
            feature_0 FLOAT,
            feature_1 FLOAT,
            feature_2 FLOAT,
            timestamp TIMESTAMP,
            PRIMARY KEY ((id), test_timestamp)
        ); 
        """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS spark_streams.dataframe_train (
            id UUID,
            timestamp TIMESTAMP,
            feature_0 FLOAT,
            feature_1 FLOAT,
            feature_2 FLOAT,
            label FLOAT,
            PRIMARY KEY ((id), timestamp)
        ) WITH CLUSTERING ORDER BY (timestamp DESC);
        """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS spark_streams.dataframe_test (
            id UUID,
            timestamp TIMESTAMP,
            feature_0 FLOAT,
            feature_1 FLOAT,
            feature_2 FLOAT,
            label FLOAT,
            PRIMARY KEY ((id), timestamp)
        ) WITH CLUSTERING ORDER BY (timestamp DESC);
        """)

def create_spark_connection():
    s_conn = None
    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config("spark.kubernetes.container.image", "sarahema/spark-scalable:3.6.0") \
            .config("spark.kubernetes.namespace", "default") \
            .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
            .config("spark.cassandra.connection.host", "cassandra.default.svc.cluster.local") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.cassandra.auth.username", "cassandra") \
            .config("spark.cassandra.auth.password", "cassandra") \
            .config("spark.dynamicAllocation.enabled", "true") \
            .getOrCreate()

        s_conn.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")
        print("=============================================================================================================")
        print(s_conn.sparkContext.getConf().getAll())
    except Exception as e:
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn

def connect_to_kafka(spark_conn):
    spark_df = None
    try:
        # subscribe to topic
        spark_df = spark_conn.readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', 'kafka-service.default.svc.cluster.local:9092') \
            .option('subscribe', 'data_stream') \
            .option('startingOffsets', 'earliest') \
            .load()
        print("Kafka dataframe created successfully")
    except Exception as e:
        print(f"Failed to create Kafka dataframe: {e}\n{traceback.format_exc()}")

    return spark_df


def create_cassandra_connection():
    try:
        # Connecting to the Cassandra cluster
        auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')

        cluster = Cluster(['cassandra.default.svc.cluster.local'], auth_provider=auth_provider)

        # Creating a session
        cas_session = cluster.connect()

        return cas_session
    except Exception as e:
        logging.error(f"Could not create Cassandra connection due to {e}")
        return None



def create_selection_df_from_kafka(spark_df):
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("timestamp", TimestampType(), False),
        StructField("feature_0", FloatType(), False),
        StructField("feature_1", FloatType(), False),
        StructField("feature_2", FloatType(), False),
        StructField("label", FloatType(), False),
    ])

    sel = spark_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")
    print(sel)

    return sel

if __name__ == "__main__":
    # create spark connection
    spark_conn = create_spark_connection()

    if spark_conn is not None:
        # connect to kafka with spark connection
        spark_df = connect_to_kafka(spark_conn)
        selection_df = create_selection_df_from_kafka(spark_df)
        session = create_cassandra_connection()

        if session is not None:
            #create_keyspace(session)
            create_table(session)

            logging.info("Streaming is being started...")

            streaming_query = (selection_df.writeStream.format("org.apache.spark.sql.cassandra")
                               .option('checkpointLocation', '/tmp/checkpoint')
                               .option('keyspace', 'spark_streams')
                               .option('table', 'dataframe_test')
                               .option('host', 'cassandra.default.svc.cluster.local')
                               .start())

            streaming_query.awaitTermination()
