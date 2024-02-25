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


def create_keyspace(session):
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS spark_streams
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
    """)

    print("Keyspace created successfully!")


def create_table(session):
    session.execute("""
    CREATE TABLE IF NOT EXISTS spark_streams.dataframe (
        id UUID PRIMARY KEY,
        number FLOAT);
    """)

    print("Table created successfully!")


# def insert_data(session, **kwargs):
#     print("inserting data...")

#     id_cas = datetime.datetime.now()
#     number_cas = kwargs.get('number')

#     try:
#         session.execute("""
#             INSERT INTO spark_streams.dataframe(id, number)
#                 VALUES (%s, %f)
#         """, (id_cas, number_cas))
#         print(f"Data inserted for {id_cas} {number_cas}")

#     except Exception as e:
#         logging.error(f'could not insert data due to {e}')


def create_spark_connection():
    s_conn = None

    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
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
        StructField("number", FloatType(), False)

    ])

    sel = spark_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")
    print(sel)

    return sel

def write_to_c(batch_df, batch_id):
    batch_df.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="dataframe", keyspace="spark_streams") \
        .mode("append") \
        .save()


if __name__ == "__main__":
    # create spark connection
    spark_conn = create_spark_connection()

    if spark_conn is not None:
        # connect to kafka with spark connection
        spark_df = connect_to_kafka(spark_conn)
        selection_df = create_selection_df_from_kafka(spark_df)
        # Generate ID using row_number() function
        #window_spec = Window.orderBy("number")  # You can adjust the ordering as per your requirement
        #final_df = selection_df.withColumn("id", row_number().over(window_spec))
        #final_df = selection_df.rdd.zipWithIndex().map(lambda x: (x[0]["number"], x[1])).toDF(["number", "id"])
        
        #window_spec = Window.orderBy("number")
        #final_df = selection_df.withColumn("id", row_number().over(window_spec))
        final_df = selection_df.withColumn("id", monotonically_increasing_id())
        session = create_cassandra_connection()

        if session is not None:
            create_keyspace(session)
            create_table(session)
            
            print("Streaming is being started...")

            
            streaming_query = (selection_df.writeStream.foreachBatch(write_to_c).start())   

            streaming_query.awaitTermination()