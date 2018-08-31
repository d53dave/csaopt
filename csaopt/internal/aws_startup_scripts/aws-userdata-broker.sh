#!/usr/bin/env bash

docker-run -d -p {port}:6379 REDIS_PASSWORD={password} bitnami/redis