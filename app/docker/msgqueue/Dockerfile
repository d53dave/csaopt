FROM alpine:3.6
MAINTAINER David Sere "dave@d53dev.net"

ARG capnp_version=0.6.1
ARG data_port=5353
ARG management_port=5354

ENV capnp_version=$capnp_version
ENV data_port=$data_port
ENV management_port=$management_port
ENV csaopt_dir=/opt/csaopt-zmq

RUN apk update && apk add linux-headers git make curl g++ python3 libzmq python3-dev
RUN curl -O https://capnproto.org/capnproto-c++-$capnp_version.tar.gz &&\
    tar zxf capnproto-c++-$capnp_version.tar.gz &&\
    cd capnproto-c++-$capnp_version &&\
    ./configure && make -j6 && make install && rm -r *


RUN git clone https://github.com/d53dave/csaopt-zmq.git $csaopt_dir

WORKDIR $csaopt_dir

RUN pip3 install pipenv &&\
    pipenv install

RUN apk git del linux-headers make g++ python3-dev

RUN pipenv run csaopt-zmq --port-data $data_port --port-management $management_port


