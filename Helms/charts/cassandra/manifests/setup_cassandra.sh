#!/bin/bash

# this will give it a random password
kubectl apply -f cassandra-service.yaml

kubectl apply -f cassandra-statefulset.yaml