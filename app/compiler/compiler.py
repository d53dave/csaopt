import subprocess
import arrow
import os
import tempfile
import threading
import queue
import time
from pathlib import Path

def _make_temp_dir(prefix):
    return tempfile.TemporaryDirectory(prefix=prefix)

def _output_reader(proc, outq):
    for line in iter(proc.stdout.readline, b''):
        outq.put(line.decode('utf-8'))


def _which(name):
    """Find executable on system. From https://stackoverflow.com/a/377028/2822762"""
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(name)
    if fpath:
        if is_exe(name):
            return name
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, name)
            if is_exe(exe_file):
                return exe_file

    return None

class ModelCompiler():
    def __init__(self, model_proj_path, conf):
        self.model_project_path = Path(model_proj_path).resolve()
        self.cmake_exec_path = conf['build.cmake_path']

        if self.cmake_exec_path is None:
           self.cmake_exec_path = _which('cmake')

        if self.cmake_exec_path is None:
            raise AssertionError('could not locate cmake on system')
        
        print('cmake: ' + self.cmake_exec_path)
    
    def prepare_compilation(self, path):
        self.working_dir = _make_temp_dir('csaopt_')
        # proc = subprocess.Popen([self.cmake_exec_path, 'path'],
        #                     stdout=subprocess.PIPE,
        #                     stderr=subprocess.STDOUT)

    def compile(self):
        assert self.working_dir is not None
        self.compile_subproc = subprocess.Popen([self.cmake_exec_path, self.model_project_path],
                                cwd=self.working_dir.name,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        self.compile_out_q = queue.Queue()
        self.compile_thread = threading.Thread(target=_output_reader, args=(self.compile_subproc, self.compile_out_q))
        self.compile_thread.start()

    def _terminate(self):
        self.compile_subproc.terminate()

    def check_artifacts(self):
        pass

if __name__ == '__main__':
    cwd = os.getcwd()
    model_dir = Path('app/model').resolve()
    print(model_dir)
    model_compiler = ModelCompiler(model_dir, {'build.cmake_path': None})
    model_compiler.prepare_compilation(None)
    model_compiler.compile()

    time.sleep(1)
    try:
        while not model_compiler.compile_out_q.empty():
            line = model_compiler.compile_out_q.get(block=False)
            print('got line from outq: {0}'.format(line), end='')
    except queue.Empty:
        print('Finished')
    finally:
        model_compiler.compile_subproc.terminate()
        try:
            model_compiler.compile_subproc.wait(timeout=30)
            print('== subprocess exited with rc =',  model_compiler.compile_subproc.returncode)
        except subprocess.TimeoutExpired:
            print('subprocess did not terminate in time')
    model_compiler.compile_thread.join()
