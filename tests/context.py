# flake8: noqa

import os
import sys
from distutils import dir_util

sys.path.insert(0, os.path.abspath('.'))

from csaopt.instancemanager.awstools import AWSTools
from csaopt.utils import get_own_ip
from csaopt import ConsolePrinter, Context as AppContext
from csaopt.model import Model, RandomDistribution, Precision
from csaopt.model_loader.model_loader import ModelLoader, ModelValidator, ValidationError
from csaopt import Runner, ExecutionType
from csaopt.jobs.jobmanager import JobManager, Job

def copy_folder_contents(src, dest):

    try:
        dir_util.copy_tree(src, dest)
    except dir_util.DistutilsFileError as e:
        print('Error while copying folder contents from {} to {}: {}'.format(src, dest, e))
        raise
