# flake8: noqa

import os
import sys
from distutils import dir_util

sys.path.insert(0, os.path.abspath('.'))

from app.instancemanager.awstools import AWSTools
from app.msgqclient import Worker
from app.msgqclient.client import QueueClient
from app.utils import get_own_ip

def copy_folder_contents(src, dest):

    try:
        dir_util.copy_tree(src, dest)
    except dir_util.DistutilsFileError as e:
        print('Error while copying folder contents from {} to {}: {}'.format(src, dest, e))
        raise