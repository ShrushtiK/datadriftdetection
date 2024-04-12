# DataAndConceptDriftDetection



## Deadline 1 - Architecture
Uploaded the architecture of the project in "Scalable Computing Project Architecture.pdf"

## Deadline 2 - Infrastructure
Managed to have our components aka Spark, Kafka, Cassandra and Data Generator up via docker compose and succesfully able to update Cassandra with our dataset values via a Spark job

## Deadline 3 
Created Spark job for training and testing a GBTRegressor on the dataset and check for potential drift by seeing the biggest drops in prediction accuracies. But, the event is manually triggered by "exec"-ing into the spark-master. Without the support of an event-based architecture, it seems very hard to have a functional and automated pipeline for the project. For instance
- triggering the training job once we have "enough historical data" in the database
- trigger testing once the model is prepared
- re-train the model again once the drift is detected for too long
- how to differentiate the data that the model trains on versus the once it predicts detection on (the data used for testing must also become a part of the training set once the model is being re-trained), and so on. 
For now, the testing has been done via the following   
```
docker compose up --build --scale spark-worker=4
```

## Deadline 4
- Integration of Grafana and connectivity with Cassandra
- Integration of Airflow for Spark jobs (training and testing)
- Cassandra table redesign for storing historical data and saving predictions + Cassandra partitioning (full replication)
