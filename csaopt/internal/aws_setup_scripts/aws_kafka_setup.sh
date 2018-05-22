#!/usr/bin/env bash

sudo apt-get update

# Docker
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88

sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

sudo apt update && sudo apt-get install docker-ce docker-compose -y
sudo usermod -aG docker $USER

# Docker Images
sudo docker pull wurstmeister/zookeeper:latest
sudo docker pull wurstmeister/kafka:1.1.0

# Kafka Docker
wget https://github.com/wurstmeister/kafka-docker/archive/1.1.0.tar.gz && tar xf 1.1.0.tar.gz && cd kafka-docker-1.1.0

# Kafka Setup
echo "version: '2'
services:
  zookeeper:
    image: wurstmeister/zookeeper:3.4.6
    ports:
      - '2181:2181'
  kafka:
    build: .
    ports:
      - '9092:9092'
      - '9094:9094'
    environment:
      HOSTNAME_COMMAND: curl http://169.254.169.254/latest/meta-data/public-ipv4
      KAFKA_CREATE_TOPICS: 'csaopt.management.in:1:1,csaopt.management.out:1:1,csaopt.data.in:1:1,csaopt.data.out:1:1'
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: INSIDE://:9092,OUTSIDE://_{HOSTNAME_COMMAND}:9094
      KAFKA_LISTENERS: INSIDE://:9092,OUTSIDE://:9094
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: INSIDE
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
" > docker-compose-single-broker.yml

