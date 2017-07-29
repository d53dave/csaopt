# CSAOpt - A Cloud GPU based Simulated Annealing Optimization Framework. [![Build Status](https://travis-ci.org/d53dave/csaopt.svg?branch=master)](https://travis-ci.org/d53dave/csaopt) [![Coverage Status](https://coveralls.io/repos/github/d53dave/csaopt/badge.svg?branch=master)](https://coveralls.io/github/d53dave/csaopt?branch=master)

The main premise of this framework is that a user provides the implementation for an abstract base class that describes the *standard* way of doing Simulated Annealing while CSAOpt takes care of starting, configuring and running a massively parallel flavor of Simulated Annealing on GPUs hosted in the cloud.

## Usage

TBD

## Configuration

The configuration is based on typesafes/lightbends [HOCON](https://github.com/typesafehub/config/blob/master/HOCON.md) and integrated with the excellent [pyhocon](https://github.com/chimpler/pyhocon). The main configuration (i.e. configuration for running the software) is located in `conf/csaopt.conf`. In addition, there is an internal configuration file under `app/internal/csaopt-internal.conf`, which does not need to be modified under normal circumstances. A detailed description and listing of supported configuration will follow here.

## Requirements

This software will not run on Windows out of the box, but it might run in the [WSL](https://blogs.msdn.microsoft.com/wsl). It will probably run on MacOS, but this is untested as of now. If you want to run it on a recent Linux distribution, you are in luck. Development was done on [ElementaryOS](https://elementary.io/), while the deployed AWS intances are based on Ubuntu Server 16.04 LTS.

Required software:
- Python 3.5 or higher
- [Pipenv](http://docs.pipenv.org/en/latest/) is not strictly required, but recommended
- [AWS](https://aws.amazon.com/) credentials or a local GPU capable of running [CUDA](https://www.geforce.com/hardware/technology/cuda) computations.
- [GCC](https://gcc.gnu.org/) 4.9 or later ([clang](https://clang.llvm.org/) is not yet supported, but I will be looking into that)
- [CMake](https://cmake.org/) 3.3 or higher
- Development package for [libzmq3](https://packages.ubuntu.com/search?keywords=libzmq3-dev), from your favourite package manager.

If you choose to run `csaopt` without `pipenv` and a virtual environment, you need to make sure you manually install the required Python packages, e.g. by using `pip`. You can find the exact list of dependencies in the `[packages]` section of the [Pipfile](Pipfile), and the required versions in the [Pipfile.lock](Pipfile.lock).

A special note regarding `zmq`. The guys from `zeromq` pulled off a nice stunt, as the [pyzmq](https://github.com/zeromq/pyzmq) package will try to build it's own `libzmq` Python extension if it doesn't detect `libzmq` on your system. Make sure to manually install [Cython](http://cython.org/) if you need to rely on `pyzmq` building the extension.

## Development

Currently, the python development is based on 
[pipenv](https://github.com/kennethreitz/pipenv) for 
dependencies and the virtual environment. The C++ parts are 
developed using CMake.


## Change History

> 0.1.0 Change to Python

With v0.1.0, most C++ code was abandoned. It became clear 
that writing and maintaining this piece of software in C++
was never a good idea. Or, in other words, after chasing
obscure bugs where they should not be, I gave up. The initial 
thought was not to split the codebase into multiple languages for 
the sake of the current and future developers and maintainers. 
This split will gradually be introduced, resulting, ideally, in
a structure where all glue code, i.e. config parsing, command line 
interface, user interaction, networking and reporting will be 
done in Python. The core concept of a user writing a small
model as C++ code which will be executed in a simulated annealing
pipeline on graphics processors will remain.

> 0.0.x C++ prototypes

Versions 0.0.x were prototypes written in C++, 
including the proof of concept which was demo-ed to 
my thesis supervisor and colleagues. These versions were
undocumented and development was sporadic. Most changes
did not make it into version control and features
were added and abandoned at will.

