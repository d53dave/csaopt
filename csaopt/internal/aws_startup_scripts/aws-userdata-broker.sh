#!/usr/bin/env bash

docker-run -d -p {port}:{port} -e REDIS_PASSWORD={password} bitnami/redis