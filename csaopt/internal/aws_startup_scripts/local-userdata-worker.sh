#!/bin/bash

{debug} NUMBA_ENABLE_CUDASIM

# Get Image
docker pull d53dave/csaopt-worker:1.0.0

# Run
docker run -d {debug_env} d53dave/csaopt-worker