FROM bitnami/spark:latest

WORKDIR /usr/app

COPY spark_stream.py spark_stream.py

COPY submit_job.sh submit_job.sh

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

CMD ["/usr/app/submit_job.sh"]
               