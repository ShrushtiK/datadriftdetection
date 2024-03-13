from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import current_timestamp
from datetime import datetime

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("Testing Model") \
    .config("spark.cassandra.connection.host", "cassandra") \
    .config("spark.cassandra.connection.port", "9042") \
    .config("spark.cassandra.auth.username", "cassandra") \
    .config("spark.cassandra.auth.password", "cassandra") \
    .config("spark.num.executors", '2') \
    .getOrCreate()

# Load the trained model
model_path = "/usr/app/model"
model = PipelineModel.load(model_path)

# Load the trained RMSE value for comparison (optional, depending on your drift detection logic)
rmse_path = "/usr/app/rmse_train.txt"
with open(rmse_path, "r") as file:
    trained_rmse = float(file.read())

# Read test data from Cassandra, ordered by timestamp
test_data = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="dataframe_test", keyspace="spark_streams") \
    .load() \
    .orderBy("timestamp")

# Predict using the model
predictions = model.transform(test_data)

# Add the current timestamp to mark when the test was performed
predictions_with_timestamp = predictions.withColumn("test_timestamp", datetime.now().isoformat())

# Initialize evaluator for RMSE
evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")

# Calculate RMSE for the test data
test_rmse = evaluator.evaluate(predictions_with_timestamp)

print(f"Root Mean Squared Error (RMSE) on test data = {test_rmse}")

# Check for drift based on your criteria (e.g., comparison with trained RMSE)
if test_rmse > trained_rmse * 1.1:  
    print("Potential drift detected.")
    drift_data = predictions_with_timestamp.select(
        "id", "test_timestamp", "label", "prediction",
        "feature_0", "feature_1", "feature_2", "timestamp"
    )
    drift_data.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="drift_analysis", keyspace="spark_streams") \
        .save(mode="append")
