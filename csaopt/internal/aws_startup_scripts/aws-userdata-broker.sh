#!/usr/bin/env bash

docker run -d -p $external_port:6379 -e REDIS_PASSWORD=$redis_password bitnami/redis