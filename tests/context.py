# flake8: noqa

import os
import sys
import shutil

sys.path.insert(0, os.path.abspath('.'))

from app.modelcompiler.modelcompiler import ModelCompiler
from app.aws.awstools import AWSTools
from app.msgqclient.client import QueueClient


def copy_folder_contents(src, dest):
    try:
        shutil.copy(src, dest)
    # eg. source or destination doesn't exist
    except IOError as e:
        print('Error while copying folder contents from {} to {}: {}'.format(src, dest, e))
        raise