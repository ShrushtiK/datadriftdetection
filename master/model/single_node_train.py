# # clone the TensorFlow models repository
# git clone https://github.com/tensorflow/models
# cd models
#
# # checkout the specific revision that this example was based upon
# git checkout c25c3e882e398d287240f619d7f56ac5b2973b6e
#
# # download the CIFAR10 dataset to /tmp/cifar10_data
# python official/r1/resnet/cifar10_download_and_extract.py
#
# # run the example
# export TENSORFLOW_MODELS=$(pwd)
# export CIFAR_DATA=/tmp/cifar10_data/cifar-10-batches-bin
# export PYTHONPATH=${TENSORFLOW_MODELS}:$PYTHONPATH
#
# # pip install tensorflow==2.1.1 tensorflow_model_optimization==0.3.0
# python ${TENSORFLOW_MODELS}/official/benchmark/models/resnet_cifar_main.py --data_dir=${CIFAR_DATA} --num_gpus=0 --train_epochs=1
