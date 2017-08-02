import subprocess
import arrow
import os
import tempfile
import threading
import queue
import time
from pathlib import Path
import logging

logger = logging.getLogger()

# TODO: Setup flake8
# TODO: finally set up the unit tests and travis build


def _make_temp_dir(prefix):
    """Creates a new temporary directory. Note that it will be cleaned up once this goes out of scope"""
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
    def __init__(self, model_proj_path, conf, internal_conf):
        self.model_project_path = Path(model_proj_path).resolve()
        self.cmake_exec_path = conf['build.cmake_path']
        self.make_exec_path = conf['build.make_path']
        self.output_queue = queue.Queue()
        self.working_dir = _make_temp_dir('csaopt_')
        
        exec_names = internal_conf['build.exec_names']
        configured_exec_paths = self._fill_exec_paths(names, conf)
        found_exec_paths = self._find_missing_execs(names, configured_exec_paths)

        self.exec_paths = {**configured_exec_paths, **found_exec_paths}

    def _fill_exec_paths(names, config):
        """Extracts configured paths for the required executables"""

        assert names is not None
        assert config['build.exec_paths'] is not None

        return {name: config['build.exec_paths'][name] for name in names}

    def _find_missing_execs(names, exec_paths):
        """Uses `which`-like behaviour to find executables on $PATH"""
        exec_without_path = [name in names if exec_paths[name] is None]
        return {executable: which(executable) for executable in exec_without_path}

    
    def _prepare_compilation(self, path):
        """Runs Cmake"""
       
        assert self.working_dir is not None
        logger.info('Preparing model build')
        logger.debug('Invoking cmake, working_dir=', self.working_dir)
        self.compile_subproc = subprocess.Popen([self.exec_paths['cmake'], self.model_project_path],
                                cwd=self.working_dir.name,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        self.compile_thread = threading.Thread(target=_output_reader, args=(self.compile_subproc, self.output_queue))
        try:
            self.compile_thread.start()
        finally:
            model_compiler.compile_subproc.terminate()
            try:
                model_compiler.compile_subproc.wait(timeout=self.conf[])
                while not model_compiler.compile_out_q.empty():
                    line = model_compiler.compile_out_q.get(block=False)
                return  model_compiler.compile_subproc.returncode;
            except subprocess.TimeoutExpired:
                logger.error('Model build preparation step did not complete in time')
                for line in self.output_queue:
                    logger.error(line)

    def _compile(self):
        self.compile_subproc = subprocess.Popen([self.exec_paths['make'], 'j=4',
                                cwd=self.working_dir.name,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        self.compile_thread = threading.Thread(target=_output_reader, args=(self.compile_subproc, self.output_queue))
        self.compile_thread.start()
        finally:
            model_compiler.compile_subproc.terminate()
            try:
                model_compiler.compile_subproc.wait(timeout=self.conf[])
                # TODO: add verbose flag and handling
                while not model_compiler.compile_out_q.empty():
                    line = model_compiler.compile_out_q.get(block=False)
                return  model_compiler.compile_subproc.returncode;
            except subprocess.TimeoutExpired:
                logger.error('Model build step did not complete in time')
                while not model_compiler.compile_out_q.empty():
                    line = model_compiler.compile_out_q.get(block=False)
                    logger.error(line)

    def _terminate(self):
        self.compile_subproc.terminate()

    def _check_artifacts(self):
        pass

    def build(self):
        

if __name__ == '__main__':
    cwd = os.getcwd()
    model_dir = Path('app/model').resolve()
    print(model_dir)
    model_compiler = ModelCompiler(model_dir, {'build.cmake_path': None})
    model_compiler.prepare_compilation(None)
    model_compiler.compile()

    time.sleep(1)
    try:
       print('Started')
    except queue.Empty:
        print('Finished')
    finally:
       
    model_compiler.compile_thread.join()
