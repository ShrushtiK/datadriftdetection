from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import col, monotonically_increasing_id
from cassandra.cluster import Cluster
import math


# Initialize Spark Session with Cassandra support
spark = SparkSession.builder \
    .appName("Training Model") \
    .config("spark.cassandra.connection.host", "cassandra") \
    .config("spark.cassandra.connection.port", "9042") \
    .config("spark.cassandra.auth.username", "cassandra") \
    .config("spark.cassandra.auth.password", "cassandra") \
    .config("spark.num.executors", '4') \
    .config('spark.dynamicAllocation.enabled', 'true') \
    .config('spark.dynamicAllocation.minExecutors', '1') \
    .config('spark.dynamicAllocation.maxExecutors', '4') \
    .getOrCreate()

# Read data from Cassandra, filtering rows where "train" is True and sorting by "timestamp"
data = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="dataframe", keyspace="spark_streams") \
    .load() \
    .filter(col("train") == True) \
    .sort("timestamp") \
    .withColumn("row_id", monotonically_increasing_id())

# Calculate the total number of rows and the split index
total_rows = data.count()
split_index = int(total_rows * 0.7)

# Split the data into training and test sets based on the row_id
trainingData = data.filter(col("row_id") < split_index).drop("row_id")
testData = data.filter(col("row_id") >= split_index).drop("row_id")

# Prepare the VectorAssembler as part of the pipeline stages
featureAssembler = VectorAssembler(
    inputCols=["feature_0", "feature_1", "feature_2"], 
    outputCol="features")

# Configure GBTRegressor
gbt = GBTRegressor(featuresCol="features", labelCol="label", maxIter=10)

# Chain VectorAssembler and GBT model in a Pipeline
pipeline = Pipeline(stages=[featureAssembler, gbt])

# Train model
model = pipeline.fit(trainingData)

# Initialize evaluator
evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")

# Evaluate training data RMSE
trained_rmse = evaluator.evaluate(model.transform(trainingData))
print(f"Root Mean Squared Error (RMSE) on training data = {trained_rmse}")


# Initialize the processed count
processed_count = 0

def evaluate_and_detect_drift(new_data, batch_size=5, drift_threshold=0.2):
    num_batches = math.ceil(new_data.count() / batch_size)

    for i in range(num_batches):
        start_row_id = i * batch_size
        end_row_id = start_row_id + batch_size
        
        batch_data = new_data.filter((col("row_id") >= start_row_id) & (col("row_id") < end_row_id))
        
        if batch_data.count() > 0:
            predictions = model.transform(batch_data)
            batch_rmse = evaluator.evaluate(predictions)
            print(f"Batch {i+1} RMSE: {batch_rmse}, Trained RMSE: {trained_rmse}")
            
            if trained_rmse - batch_rmse > trained_rmse * drift_threshold:
                print("Possible drift detected due to sudden drop in RMSE.")
        else:
            print(f"No data in batch {i+1}, skipping evaluation.")



# Fetch all data points with train = False and sort by timestamp
new_data_all = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="dataframe", keyspace="spark_streams") \
    .load() \
    .filter(col("train") == False) \
    .sort("timestamp") \
    .withColumn("row_id", monotonically_increasing_id())  # Ensure this line is added


# Evaluate all new data in batches for drift
evaluate_and_detect_drift(new_data_all, batch_size=50, drift_threshold=0.3)

# Stop Spark Session
spark.stop()