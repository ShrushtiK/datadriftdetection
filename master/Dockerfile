FROM bitnami/spark:latest

WORKDIR /usr/app

COPY model/gbt_model.py gbt_model.py

COPY submit_job.sh submit_job.sh

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

#RUN chmod +x submit_job.sh

CMD ["/usr/app/submit_job.sh"]

# CMD ["bin/spark-class", "org.apache.spark.deploy.master.Master"]
# CMD 
               