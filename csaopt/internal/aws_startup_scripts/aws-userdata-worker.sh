#!/bin/bash

docker pull d53dave/csaopt-worker:latest

# Run
docker run  --runtime=nvidia -d        \
    -e NUMBA_ENABLE_CUDASIM={debug}    \
    -e REDIS_HOST={redis_host}         \
    -e REDIS_PORT={redis_port}         \
    -e REDIS_PASSWORD={redis_password} \
    d53dave/csaopt-worker 