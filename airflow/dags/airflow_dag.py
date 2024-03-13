from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.apache.cassandra.hooks.cassandra import CassandraHook
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.models import Connection
from airflow import settings

# Default arguments for the DAG
default_args = {
    'start_date': datetime.now() - timedelta(days=1),
    'catchup': False,
}

# DAG definition
dag = DAG(
    'Drift_detection',
    default_args=default_args,
    description='Drift detection workflow',
    schedule_interval='@once',
)

# Setup Spark and Cassandra connections
session = settings.Session()

spark_conn_id = 'spark_default'
spark_conn = Connection(
    conn_id=spark_conn_id,
    conn_type='spark',
    host='spark://spark-master:7077'
)
if not session.query(Connection).filter(Connection.conn_id == spark_conn_id).first():
    session.add(spark_conn)

cassandra_conn_id = 'cassandra_default'
cassandra_conn = Connection(
    conn_id=cassandra_conn_id,
    conn_type='cassandra',
    host='cassandra',
    port=9042,
    login='cassandra',
    password='cassandra'
)
if not session.query(Connection).filter(Connection.conn_id == cassandra_conn_id).first():
    session.add(cassandra_conn)

session.commit()

# Function to trigger Spark test job and check the count
def trigger_spark_test_and_check(**kwargs):
    cassandra_hook = CassandraHook(cassandra_conn_id='cassandra_default')
    session = cassandra_hook.get_conn()
    spark_submit = SparkSubmitOperator(
        task_id='trigger_spark_test',
        application='jobs/spark_test.py',
        conn_id='spark_default',
        packages='com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12',    
        dag=dag,
    )

    # Loop to trigger Spark test and check condition
    while True:
        spark_submit.execute(context=kwargs)
        query = "SELECT COUNT(DISTINCT test_timestamp) FROM spark_streams.drift_analysis;"
        count = session.execute(query).one()[0]
        if count >= 3:
            break

def copy_records_to_train(**kwargs):
    cassandra_hook = CassandraHook(cassandra_conn_id='cassandra_default')
    session = cassandra_hook.get_conn()
    copy_query = "INSERT INTO spark_streams.dataframe_train SELECT * FROM spark_streams.dataframe_test;"
    clear_query = "TRUNCATE spark_streams.dataframe_test;"
    session.execute(copy_query)
    session.execute(clear_query)

# Task definitions
start = DummyOperator(task_id='start', dag=dag)

trigger_spark_train = SparkSubmitOperator(
    task_id='trigger_spark_train',
    application='jobs/spark_train.py',
    conn_id=spark_conn_id,
    packages='com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,saurfang:spark-sas7bdat:3.0.0-s_2.12',
    dag=dag,
)

trigger_test_and_check = PythonOperator(
    task_id='trigger_spark_test_and_check',
    python_callable=trigger_spark_test_and_check,
    dag=dag,
)

copy_to_train_task = PythonOperator(
    task_id='copy_records_to_train',
    python_callable=copy_records_to_train,
    dag=dag,
)

end = DummyOperator(task_id='end', dag=dag)

trigger_next_run = TriggerDagRunOperator(
    task_id='trigger_next_run',
    trigger_dag_id='Drift_detection',  # Ensure this is the correct DAG ID to trigger
    dag=dag,
)

# DAG dependencies
start >> trigger_spark_train >> trigger_test_and_check >> copy_to_train_task >> end >> trigger_next_run
