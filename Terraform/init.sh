#!/bin/bash

# Script to set up basics for repository

if [ ! -f "secrets.auto.tfvars.json" ]
then
    cp secrets.auto.tfvars.json.example secrets.auto.tfvars.json
fi

if [ ! -f "locals.auto.tfvars.json" ]
then
    cp locals.auto.tfvars.json.example locals.auto.tfvars.json
fi

if [ ! -f "id_rsa" ]
then
    # if running this on windows ssh-keygen -b 4096 -t rsa -f ./id_rsa -q -N `"`"
    ssh-keygen -b 4096 -t rsa -f ./id_rsa -q -N ""
fi
