#!/bin/bash

docker pull d53dave/csaopt-worker:0.1.1

docker run --runtime=nvidia -d         \
    -e NUMBA_ENABLE_CUDASIM=$debug     \
    -e REDIS_HOST=$redis_host          \
    -e REDIS_PORT=$redis_port          \
    -e REDIS_PWD=$redis_password  \
    -e WORKER_QUEUE_ID=`curl -s http://169.254.169.254/latest/meta-data/instance-id` \
    d53dave/csaopt-worker:0.1.1