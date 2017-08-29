FROM nvidia/cuda:8.0-devel-ubuntu16.04
MAINTAINER David Sere "dave@d53dev.net"

ARG zmq_ip=127.0.0.1
ARG data_port=5353
ARG management_port=5354

ENV zmq_ip=$zmq_ip
ENV data_port=$data_port
ENV management_port=$management_port
ENV csaopt_dir /opt/csaopt-worker



RUN git clone https://github.com/d53dave/csaopt-zmq.git $csaopt_dir
WORKDIR $csaopt_dir

RUN cmake . && make -j6
RUN ./csaopt-worker --zmq-ip $zmq_ip --port-data $data_port --port-maintenance $management_port
