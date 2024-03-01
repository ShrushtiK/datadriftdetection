FROM bitnami/spark:latest

WORKDIR /usr/app

#COPY spark_stream.py spark_stream.py

COPY model/model_predict.sh model_predict_single_node.sh
COPY model/data_setup.py data_setup.py
COPY model/model_mnist.py model_mnist.py

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

CMD ["/usr/app/model_predict_single_node.sh"]

# CMD ["bin/spark-class", "org.apache.spark.deploy.master.Master"]
# CMD 
               