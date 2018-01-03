FROM alpine:3.6
LABEL maintainer="David Sere <dave@d53dev.net>"

ENV csaopt_dir=/opt/csaopt-zmq

RUN apk update && apk add git
RUN wget http://repo.continuum.io/miniconda/Miniconda3-3.7.0-Linux-x86_64.sh -O ~/miniconda.sh && \
    sh ~/miniconda.sh -b -p $HOME/miniconda && \
    export PATH="$HOME/miniconda/bin:$PATH" && \
    conda config --set always_yes yes --set changeps1 no && \
    conda update -q conda && conda info -a 

RUN git clone https://github.com/d53dave/csaopt-zmq.git $csaopt_dir

WORKDIR $csaopt_dir

RUN conda create -q -n csaopt-env -f environment.yaml
RUN source activate csaopt-env
RUN python setup.py install

RUN apk git del python3-dev

RUN pipenv run csaopt-zmq --port-data $data_port --port-management $management_port


