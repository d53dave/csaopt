import os
import sys
sys.path.insert(0, os.path.abspath('.'))
print('test path: ', os.path.abspath('.'))

from app.modelcompiler.modelcompiler import ModelCompiler