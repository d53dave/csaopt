# CSAOpt - A Cloud GPU based Simulated Annealing Optimization Framework.

The main premise of this framework is that a user provides the implementation for an abstract base class that describes the *standard* way of doing Simulated Annealing while CSAOpt takes care of starting, configuring and running a massively parallel flavor of Simulated Annealing on GPUs hosted in the cloud.

## Usage

TBD

## Configuration

The main configuration file (i.e. configuration for running the software) is located in `conf/csaopt.conf`. In addition, there is an internal configuration file under `app/internal/csaopt-internal.conf`, which does not need to be touched unter normal circumstances. A detailed description and listing of supported configuration will follow here.

## Requirements

TBD

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

