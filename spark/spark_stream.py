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


# def create_keyspace(session):
#     session.execute("""
#         CREATE KEYSPACE IF NOT EXISTS spark_streams
#         WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '3'};
#     """)

#     print("Keyspace created successfully!")


def create_table(session):
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


# def insert_data(session, **kwargs):
#     print("inserting data...")
#
#     id_cas = datetime.datetime.now()
#     data_points_cas = kwargs.get('data_point') # CHANGE 5
#     print("AAAAAAAAAAAAAASDDL: ", data_points_cas)
#     # CHANGE 9: in case of batch data, take each data point
#     for data_point in data_points_cas:
#         # CHANGE 6: break the input into x features and 1 label
#         fields = data_point.split(",")
#
#         try:
#             # CHANGE 8
#             session.execute("""
#                 INSERT INTO spark_streams.dataframe(id, feature_1, feature_2, feature_3, label)
#                     VALUES (%s, %f)
#             """, (id_cas, fields[0], fields[1], fields[2], fields[3]))
#             # TODO: the above cannot be dynamic, because it depends on the table structure
#             logging.info(f"Data inserted for {id_cas} {fields[0]} {fields[1]} {fields[2]} {fields[3]}")
#
#         except Exception as e:
#             logging.error(f'could not insert data due to {e}')



def create_spark_connection():
    s_conn = None

    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
            .config('spark.dynamicAllocation.enabled', 'true') \
            .config("spark.num.executors", '2') \
            .config('spark.dynamicAllocation.minExecutors', '1') \
            .config('spark.dynamicAllocation.maxExecutors', '2') \
            .config('spark.cassandra.connection.host', 'cassandra') \
            .getOrCreate()

        s_conn.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")
    except Exception as e:
        print(s_conn)
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn


def connect_to_kafka(spark_conn):
    spark_df = None
    try:
        # subscribe to topic
        spark_df = spark_conn.readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', 'broker:29092') \
            .option('subscribe', 'data_stream') \
            .option('startingOffsets', 'earliest') \
            .load()
        print("kafka dataframe created successfully")
    except Exception as e:
        print(f"Failed to create Kafka dataframe: {e}\n{traceback.format_exc()}")

    return spark_df


def create_cassandra_connection():
    try:
        # connecting to the cassandra cluster
        cluster = Cluster(['cassandra'])

        cas_session = cluster.connect()

        return cas_session
    except Exception as e:
        logging.error(f"Could not create cassandra connection due to {e}")
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
                               .start())

            streaming_query.awaitTermination()
