import subprocess
import os
import tempfile
import threading
import queue
import time
from pathlib import Path
import logging
from pyhocon import ConfigTree

from typing import Dict
from typing import Optional
from typing import List

logger = logging.getLogger()

# TODO: finally set up the unit tests and travis build


def _make_temp_dir(prefix: str) -> tempfile.TemporaryDirectory:
    """Creates a new temporary directory. Note that it will be cleaned up once this goes out of scope"""
    return tempfile.TemporaryDirectory(prefix=prefix)


def _output_reader(proc: subprocess.Popen, outq: queue.Queue) -> None:
    for line in iter(proc.stdout.readline, b''):
        outq.put(line.decode('utf-8'))


def _which(name: str) -> Optional[str]:
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
        self.required_artifacts = internal_conf['build.required_artifacts']
        self.make_timeout = internal_conf['build.timeouts.make']
        self.cmake_timeout = internal_conf['build.timeouts.cmake']

        assert self.required_artifacts is not None
        assert len(self.required_artifacts) > 0

        exec_names = internal_conf['build.exec_names']
        configured_exec_paths = self._fill_exec_paths(exec_names, conf)
        found_exec_paths = self._find_missing_execs(exec_names, configured_exec_paths)

        self.exec_paths = {**configured_exec_paths, **found_exec_paths}

        # Todo verify that all executables have paths, die otherwise

    def _fill_exec_paths(self, names: List[str], config: ConfigTree) -> Dict[str, str]:
        """Extracts configured paths for the required executables"""

        assert names is not None
        assert config['build.exec_paths'] is not None

        return {name: config['build.exec_paths'][name] for name in names}

    def _find_missing_execs(self, names: List[str], exec_paths: Dict[str, str]) -> Dict[str, str]:
        """Uses `which`-like behaviour to find executables on $PATH"""

        exec_without_path = [name for name in names if not exec_paths[name]]
        return {executable: _which(executable) for executable in exec_without_path}

    def _prepare_compilation(self, path: str) -> int:
        """Runs Cmake and """

        assert self.working_dir is not None
        logger.info('Preparing model build')
        logger.debug('Invoking cmake, working_dir=', self.working_dir)
        self.compile_subproc = subprocess.Popen(
                                [self.exec_paths['cmake'], self.model_project_path],
                                cwd=self.working_dir.name,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        self.compile_thread = threading.Thread(target=_output_reader, args=(self.compile_subproc, self.output_queue))
        try:
            self.compile_thread.start()
        finally:
            self.compile_subproc.terminate()
            try:  # TODO: Add timeouts from conf
                self.compile_subproc.wait(timeout=self.cmake_timeout)
                while not self.output_queue.empty():
                    line = self.output_queue.get(block=False)
                return self.compile_subproc.returncode
            except subprocess.TimeoutExpired:
                logger.error('Model build preparation step did not complete in time')
                for line in self.output_queue:
                    logger.error(line)
                return -1

    def _compile(self) -> int:
        self.compile_subproc = subprocess.Popen(
                                [self.exec_paths['make'], 'j4'],
                                cwd=self.working_dir.name,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        self.compile_thread = threading.Thread(target=_output_reader, args=(self.compile_subproc, self.output_queue))
        try:
            self.compile_thread.start()
        finally:
            model_compiler.compile_subproc.terminate()
            try:
                model_compiler.compile_subproc.wait(timeout=self.make_timeout)
                # TODO: add verbose flag and handling
                while not model_compiler.output_queue.empty():
                    line = model_compiler.output_queue.get(block=False)
                return model_compiler.compile_subproc.returncode
            except subprocess.TimeoutExpired:
                logger.error('Model build step did not complete in time')
                while not model_compiler.output_queue.empty():
                    line = model_compiler.output_queue.get(block=False)
                    logger.error(line)
                return -1

    def _terminate(self) -> None:
        self.compile_subproc.terminate()

    def _check_artifacts(self) -> None:
        for artifact in self.required_artifacts:
            artifact_path = os.path.join(self.working_dir, artifact)
            logger.debug('Model compiler verifying artifact {}'.format(artifact_path))
            if os.path.isfile(artifact_path):
                if not os.path.getsize(artifact_path) > 0:
                    raise AssertionError('Artifact {} was produced, but is empty'.format(artifact))
            else:
                raise AssertionError('Could not verify that build step produced {}'.format(artifact))

    def build(self) -> Dict[str, str]:
        pass


if __name__ == '__main__':
    cwd = os.getcwd()
    model_dir = Path('app/model').resolve()
    print(model_dir)
    model_compiler = ModelCompiler(model_dir, {'build.cmake_path': None}, {})
    model_compiler._prepare_compilation(None)
    model_compiler._compile()

    time.sleep(1)
    try:
        print('Started')
    except queue.Empty:
        print('Finished')
    finally:
        model_compiler.compile_thread.join()
