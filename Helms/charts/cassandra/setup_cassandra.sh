#!/bin/bash

# this will give it a random password
helm install default oci://registry-1.docker.io/bitnamicharts/cassandra

# here you setup the password
helm install default \
    --set dbUser.user=cassandra,dbUser.password=cassandra \
    oci://registry-1.docker.io/bitnamicharts/cassandra


# connect to the cassandra client pod with the correct auth password
kubectl run --namespace default default-cassandra-client --rm --tty -i --restart='Never'  --env CASSANDRA_PASSWORD=cassandra  --image docker.io/bitnami/cassandra:4.1.4-debian-12-r4 -- bash 

# here the script fails although this is identical to the official documentation: connect to cassandra query language after you entered the cassandra pod
cqlsh -u cassandra -p cassandra default-cassandra 9042 
