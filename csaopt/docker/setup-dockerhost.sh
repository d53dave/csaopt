# TODO: this should at the very least handle ubuntu/debian and fedora/centos
# Checking via lsb_release and switch package manager

# Note, this assumes root privileges!

apt-get install -y wget

wget -O - https://get.docker.com/ | sh

docker pull nvidia/cuda:8.0-devel

