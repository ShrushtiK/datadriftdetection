CREATE KEYSPACE IF NOT EXISTS spark_streams WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};

USE spark_streams;

CREATE TABLE IF NOT EXISTS spark_streams.drift_analysis (
    id UUID,
    label FLOAT,
    prediction FLOAT,
    feature_0 FLOAT,
    feature_1 FLOAT,
    feature_2 FLOAT,
    timestamp TIMESTAMP,
    train_auc FLOAT,
    test_auc FLOAT,
    drift BOOLEAN,
    PRIMARY KEY ((id), timestamp)
); 

CREATE TABLE IF NOT EXISTS spark_streams.dataframe_train (
    id UUID,
    timestamp TIMESTAMP,
    feature_0 FLOAT,
    feature_1 FLOAT,
    feature_2 FLOAT,
    label FLOAT,
    PRIMARY KEY ((id), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);

CREATE TABLE IF NOT EXISTS spark_streams.dataframe_test (
    id UUID,
    timestamp TIMESTAMP,
    feature_0 FLOAT,
    feature_1 FLOAT,
    feature_2 FLOAT,
    label FLOAT,
    PRIMARY KEY ((id), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);

COPY spark_streams.dataframe_train (id, timestamp, feature_0, feature_1, feature_2, label) FROM '/usr/src/app/training.csv' WITH HEADER = TRUE;

       
