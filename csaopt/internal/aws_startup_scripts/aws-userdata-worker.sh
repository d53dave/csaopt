#!/bin/bash

# Get Image
docker pull d53dave/csaopt-worker:1.0.0

# Run
docker run -d d53dave/csaopt-worker 