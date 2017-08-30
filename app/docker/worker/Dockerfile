FROM nvidia/cuda:8.0-devel
MAINTAINER David Sere "dave@d53dev.net"

ARG capnp_version=0.6.1
ARG msgq_ip=127.0.0.1
ARG data_port=5353
ARG management_port=5354

ENV capnp_version=$capnp_version
ENV data_port=$data_port
ENV management_port=$management_port
ENV csaopt_dir=/opt/csaopt-worker

RUN apt-get update && apt-get install -y git libzmq3-dev  &&\
    rm -rf /var/lib/apt/lists/*

RUN curl -O https://capnproto.org/capnproto-c++-$capnp_version.tar.gz &&\
    tar zxf capnproto-c++-$capnp_version.tar.gz &&\
    cd capnproto-c++-$capnp_version &&\
    ./configure && make -j6 && make install && rm -r *

# TODO: replace git clone by a curl of release tar on girhub
RUN git clone https://github.com/d53dave/csaopt-worker.git $csaopt_dir

WORKDIR $csaopt_dir

RUN cmake . &&\
    make

RUN apt-get remove --purge git

RUN ./csaopt-worker --host-msgq $msgq_ip --port-data $data_port --port-management $management_port
