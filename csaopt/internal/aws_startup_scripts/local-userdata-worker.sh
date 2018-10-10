#!/bin/bash

# Get Image
docker pull d53dave/csaopt-worker:0.1.1

# Run 
# Template engine needs to replace runtime with "--runtime=nvidia" or empty string
# and debug_env with "1" or "false".
docker run $runtime_complete_flag -d -e NUMBA_ENABLE_CUDASIM=$debug -e WORKER_QUEUE_ID=$worker_queue_id d53dave/csaopt-worker:0.1.1