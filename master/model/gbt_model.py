# Import necessary libraries
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import rand

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("PySpark GBT Regression Demo") \
    .getOrCreate()

# Generate or load data
data = spark.range(0, 100).select("id", (rand(seed=42) * 100).alias("feature1"), (rand(seed=27) * 50).alias("label"))

# Prepare data for training
featureAssembler = VectorAssembler(inputCols=["feature1"], outputCol="assembled_features")
data = featureAssembler.transform(data).withColumnRenamed("assembled_features", "features")

# Split the data into training and test sets
(trainingData, testData) = data.randomSplit([0.7, 0.3])

# Configure GBTRegressor
gbt = GBTRegressor(featuresCol="features", labelCol="label", maxIter=10)

# Chain vectorAssembler and GBT model in a Pipeline
pipeline = Pipeline(stages=[featureAssembler, gbt])

# Train model
model = pipeline.fit(trainingData)

# Make predictions
predictions = model.transform(testData)

# Select example rows to display
predictions.select("prediction", "label", "features").show(5)

# Select (prediction, true label) and compute test error
evaluator = RegressionEvaluator(
    labelCol="label", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)
print("Root Mean Squared Error (RMSE) on test data = %g" % rmse)

# Stop Spark Session
spark.stop()
