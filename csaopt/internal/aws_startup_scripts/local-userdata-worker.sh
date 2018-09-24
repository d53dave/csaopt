#!/bin/bash

# Get Image
docker pull d53dave/csaopt-worker:1.0.0

# Run 
# Template engine needs to replace runtime with "--runtime=nvidia" or empty string
# and debug_env with "1" or "false".
docker run $runtime_complete_flag -d -e NUMBA_ENABLE_CUDASIM=$debug d53dave/csaopt-worker