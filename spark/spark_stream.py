import logging
import datetime
from cassandra.cluster import Cluster
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import *


def create_keyspace(session):
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS spark_streams
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
    """)

    print("Keyspace created successfully!")


def create_table(session):
    # CHANGE 4 # TODO: cassandra does not have datatype NUMBER(?)
    session.execute("""
    CREATE TABLE IF NOT EXISTS spark_streams.dataframe (
        id UUID PRIMARY KEY,
        feature1 FLOAT,
        feature2 FLOAT,
        feature3 FLOAT,
        label NUMBER);
    """)

    print("Table created successfully!")


def insert_data(session, **kwargs):
    print("inserting data...")

    id_cas = datetime.datetime.now()
    data_points_cas = kwargs.get('data_point') # CHANGE 5

    # CHANGE 9: in case of batch data, take each data point
    for data_point in data_points_cas:
        # CHANGE 6: break the input into x features and 1 label
        fields = data_point.split(",")

        try:
            # CHANGE 8
            session.execute("""
                INSERT INTO spark_streams.dataframe(id, feature1, feature2, feature3, label)
                    VALUES (%s, %f)
            """, (id_cas, fields[0], fields[1], fields[2], fields[3]))
            # TODO: the above cannot be dynamic, because it depends on the table structure
            logging.info(f"Data inserted for {id_cas} {fields[0]} {fields[1]} {fields[2]} {fields[3]}")

        except Exception as e:
            logging.error(f'could not insert data due to {e}')


def create_spark_connection():
    s_conn = None

    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.13:3.4.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.13:3.4.1") \
            .config('spark.cassandra.connection.host', 'localhost') \
            .getOrCreate()

        s_conn.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")
    except Exception as e:
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn


def connect_to_kafka(spark_conn):
    spark_df = None
    try:
        # subscribe to topic
        spark_df = spark_conn.readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', 'localhost:9092') \
            .option('subscribe', 'data_stream') \
            .option('startingOffsets', 'earliest') \
            .load()
        logging.info("kafka dataframe created successfully")
    except Exception as e:
        logging.warning(f"kafka dataframe could not be created because: {e}")

    return spark_df


def create_cassandra_connection():
    try:
        # connecting to the cassandra cluster
        cluster = Cluster(['localhost'])

        cas_session = cluster.connect()

        return cas_session
    except Exception as e:
        logging.error(f"Could not create cassandra connection due to {e}")
        return None


def create_selection_df_from_kafka(spark_df):
    schema = StructType([
        StructField("id", StringType(), False),
        # CHANGE 7
        StructField("feature1", FloatType(), False),
        StructField("feature2", FloatType(), False),
        StructField("feature3", FloatType(), False),
        StructField("label", IntegerType(), False)
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
            create_keyspace(session)
            create_table(session)

            logging.info("Streaming is being started...")

            streaming_query = (selection_df.writeStream.format("org.apache.spark.sql.cassandra")
                               .option('checkpointLocation', '/tmp/checkpoint')
                               .option('keyspace', 'spark_streams')
                               .option('table', 'dataframe')
                               .start())

            streaming_query.awaitTermination()