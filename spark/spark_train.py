from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import row_number, col, monotonically_increasing_id
from cassandra.cluster import Cluster
import math
#import joblib
from pyspark.sql.window import Window


# Initialize Spark Session with Cassandra support
spark = SparkSession.builder \
    .appName("Training Model") \
    .config("spark.kubernetes.container.image", "sarahema/spark-scalable:3.4.0") \
    .config("spark.kubernetes.namespace", "default") \
    .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                                   "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
    .config("spark.cassandra.connection.host", "cassandra.default.svc.cluster.local") \
    .config("spark.cassandra.connection.port", "9042") \
    .config("spark.cassandra.auth.username", "cassandra") \
    .config("spark.cassandra.auth.password", "cassandra") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .getOrCreate()

data = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="dataframe_train", keyspace="spark_streams", host="cassandra.default.svc.cluster.local") \
    .load()

sorted_data = data.sort("timestamp")

windowSpec = Window.orderBy("timestamp")
data_with_row_number = sorted_data.withColumn("row_num", row_number().over(windowSpec))

total_rows = data_with_row_number.count()

# Calculate the split index for training and testing data, i.e 70-30 split
split_index = int(total_rows * 0.7)

# Split the data into training and testing sets
trainingData = data_with_row_number.filter(col("row_num") <= split_index).drop("row_num")
testData = data_with_row_number.filter(col("row_num") > split_index).drop("row_num")

# Repartition the DataFrame to ensure it's distributed across executors
trainingData = trainingData.repartition("timestamp")
testData = testData.repartition("timestamp")

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

#Save trained model
model_path = "/usr/app/model"
model.write().overwrite().save(model_path)

# Save the training RMSE value
rmse_path = "/usr/app/rmse_train.txt"
with open(rmse_path, "w") as file:
    file.write(str(trained_rmse))