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

sudo apt update && sudo apt install docker-ce -y
sudo usermod -aG docker $USER

# Nvidia Docker
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update && sudo apt-get install nvidia-docker2 -y
sudo pkill -SIGHUP dockerd

# Docker Images
sudo docker pull nvidia/cuda:8.0-runtime
sudo docker pull alpine:3.7

# CUDA
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update && sudo apt install nvidia-367

# Test NVidia Driver
docker run --runtime=nvidia --rm nvidia/cuda nvidia-smi
# or
nvidia-docker run --rm -ti ryanolson/device-query

docker pull d53dave/csaopt-worker:latest

