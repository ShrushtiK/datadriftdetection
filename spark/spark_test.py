from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql.functions import lit

import mlflow
import mlflow.spark
import os

mlflow.set_tracking_uri("http://mlflow-service.default.svc.cluster.local:5000")
mlflow.set_experiment("Data drift")


os.getenv("AWS_ACCESS_KEY_ID")
os.getenv("AWS_SECRET_ACCESS_KEY")


# Initialize Spark Session
def getSparkSession():
    spark = SparkSession.builder \
        .appName("Testing Model") \
        .config("spark.kubernetes.container.image", "shrushti5/custom-spark:2.15") \
        .config("spark.kubernetes.namespace", "default") \
        .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
        .config("spark.cassandra.connection.host", "cassandra.default.svc.cluster.local") \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.cassandra.auth.username", "cassandra") \
        .config("spark.cassandra.auth.password", "cassandra") \
        .config("spark.dynamicAllocation.enabled", "true") \
        .getOrCreate()
    #spark.sparkContext.setLogLevel("ERROR")

    hadoopConf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoopConf.set('fs.s3a.access.key', os.environ["AWS_ACCESS_KEY_ID"])
    hadoopConf.set('fs.s3a.secret.key', os.environ["AWS_SECRET_ACCESS_KEY"])
    hadoopConf.set('fs.s3.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
    hadoopConf.set("fs.s3a.connection.ssl.enabled", "true")
    hadoopConf.set("fs.s3a.path.style.access", 'true')

    return spark    

spark = getSparkSession()

runs = mlflow.search_runs(search_all_experiments=True)
latest_run = runs.iloc[0]

auc = latest_run["metrics.auc"]
print(f"Area Under ROC on train data = {auc}")
#model_url = f"runs://{latest_run.run_id}/model"
model_url = f"{latest_run.artifact_uri}/model"

model = mlflow.spark.load_model(model_url)

# Load the trained model
# model_path = "/usr/app/model"
# model = PipelineModel.load(model_path)

# Load the trained RMSE value for comparison (optional, depending on your drift detection logic)
# rmse_path = "/usr/app/rmse_train.txt"
# with open(rmse_path, "r") as file:
#     trained_rmse = float(file.read())

# Read test data from Cassandra, ordered by timestamp
testData = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="dataframe_test", keyspace="spark_streams", host="cassandra.default.svc.cluster.local") \
    .load() \
    .orderBy("timestamp")

testData = testData.repartition("label")

# Predict using the model
predictions = model.transform(testData)

# Initialize evaluator 
evaluator = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")

# Calculate RMSE for the test data
test_auc = evaluator.evaluate(predictions)

print(f"Area Under ROC on test data = {test_auc}")

drift = False

if abs(test_auc - auc) > 0.05:
    print("Potential Drift Detected")
    drift = True
else:
    print("No Drift Detected")

#predictions.printSchema()
#print(predictions.columns)
#print(predictions.select("prediction").show(50, truncate=False))
predictions_for_drift = predictions \
    .withColumn('train_auc', lit(auc)) \
    .withColumn('test_auc', lit(test_auc)) \
    .withColumn('drift', lit(drift))

drift_data = predictions_for_drift.select("id", "label", "prediction", "feature_0", "feature_1", "feature_2", "timestamp", "train_auc", "test_auc", "drift")
drift_data.write \
    .format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .option('keyspace', 'spark_streams') \
    .option('table', 'drift_analysis') \
    .option('host', 'cassandra.default.svc.cluster.local') \
    .save()
    
                               

# Check for drift based on your criteria (e.g., comparison with trained RMSE)
# if test_rmse > trained_rmse * 1.1:  
#     print("Potential drift detected.")
#     drift_data = predictions_with_timestamp.select(
#         "id", "test_timestamp", "label", "prediction",
#         "feature_0", "feature_1", "feature_2", "timestamp"
#     )
#     drift_data.write \
#         .format("org.apache.spark.sql.cassandra") \
#         .options(table="drift_analysis", keyspace="spark_streams", host="cassandra.default.svc.cluster.local") \
#         .save(mode="append")
# else:
#     print("No drift detected")

