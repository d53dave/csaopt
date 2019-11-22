__version__ = '0.1.0'
__appname__ = 'CSAOpt: Cloud based, GPU accelerated Simulated Annealing'

import asyncio
import logging
import shutil
import sys
import subprocess
import unicodedata
import re
import os
import time
import pathlib
import better_exceptions

from pyhocon import ConfigTree
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job as ApJob
from asyncio.selector_events import BaseSelectorEventLoop
from typing import Dict, Optional, List, Any
from sty import fg, ef, rs, Rule, Render
from datetime import datetime, timedelta
from async_timeout import timeout

from .model_loader.model_loader import ModelLoader
from .model import Model
from .utils import get_configs, internet_connectivity_available
from .instancemanager.instancemanager import InstanceManager
from .instancemanager.awstools import AWSTools
from .jobs.jobmanager import Job, JobManager, ExecutionType
from .broker import Broker

better_exceptions.hook()

# logging.basicConfig(level='INFO')
log = logging.getLogger('csaopt.Runner')
fg.set_rule('csaopt_magenta', Rule(Render.rgb_fg, 199, 51, 147))

# log.setLevel(logging.DEBUG)

logging.getLogger('botocore').setLevel(logging.WARN)
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARN)


class ConsolePrinter:

    status_done = 'Done.'
    status_failed = 'Failed.'
    __ANSI_escape_re = re.compile(r'[\x1B|\x1b]\[[0-?]*[ -/]*[@-~]')

    def __init__(self, internal_config, log_level='info') -> None:
        self.spinner_idx = 0
        self.termsize = shutil.get_terminal_size((80, 20))
        self.last_line: str = ''
        self.has_scheduled_print: bool = False
        self.print_job: Optional[ApJob] = None
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.spinner: List[str] = ['◣', '◤', '◥', '◢']
        self.log_level = log_level

        max_columns = internal_config.get('console.width_max')
        self.columns = internal_config.get('console.width_default')

        try:
            _, columns = subprocess.check_output(['stty', 'size']).split()
            if int(columns) < max_columns:
                self.columns = columns
        except Exception:
            log.exception('Could not get stty size, it seems there is no console available.')

    @staticmethod
    def _format_to_width(width: int, txt: str, status: str) -> str:
        txt_len = len(ConsolePrinter._remove_special_seqs(txt))
        status_len = len(ConsolePrinter._remove_special_seqs(status))
        if (txt_len + status_len) > width:
            return txt[0:(width - status_len - 4)] + '... ' + status

        return txt + ''.join([' '] * (width - status_len - txt_len)) + status

    @staticmethod
    def _remove_special_seqs(s):
        no_ansi = ConsolePrinter.__ANSI_escape_re.sub('', s)
        no_c = ''.join(c for c in no_ansi if unicodedata.category(c)[0] != 'C')
        return no_c

    def _advance_spinner(self):
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner)

    def print(self, txt: str) -> None:
        self._advance_spinner()
        sys.stdout.write(txt + rs.all)
        sys.stdout.flush()
        self.last_line = txt

    def println(self, txt: str) -> None:
        self.print(txt + rs.all + '\n')

    def print_magenta(self, txt: str) -> None:
        self.print(fg.csaopt_magenta + txt)

    def print_with_spinner(self, txt: str) -> None:
        self.scheduler.remove_all_jobs()
        self.last_line = txt

        self.print_job = self.scheduler.add_job(
            lambda: self.print('\r' + ConsolePrinter._format_to_width(
                self.columns,
                txt,
                fg.csaopt_magenta + self.spinner[self.spinner_idx] + '    ')),
            'interval',
            seconds=0.42,
            id='print_job',
            max_instances=1,
            next_run_time=datetime.now() + timedelta(milliseconds=50))  # run in 50ms, then periodically

    def spinner_success(self) -> None:
        # If log level < warn, just re-print with 'Done.'
        # Truncate to console width to fit message
        if self.log_level == 'info':
            if self.print_job is not None:
                self.print_job.pause()
                self.print_job.remove()
            self.scheduler.remove_all_jobs()
            self.println(
                ConsolePrinter._format_to_width(self.columns,
                                                self.last_line[0:self.columns - len(ConsolePrinter.status_done)],
                                                fg.green + ConsolePrinter.status_done))

    def spinner_failure(self) -> None:
        # If log level < warn, just re-print with 'Failed.'
        # Truncate to console width to fit message
        if self.log_level == 'info':
            self.scheduler.remove_all_jobs()
            self.println(
                ConsolePrinter._format_to_width(self.columns,
                                                self.last_line[0:self.columns - len(ConsolePrinter.status_failed)],
                                                fg.red + ConsolePrinter.status_failed))


class Runner:
    def __init__(self, model_paths: List[str], conf_paths: List[str], invocation_options: Dict[str, Any]) -> None:
        internal_conf = invocation_options['internal_conf']

        self.console_printer = ConsolePrinter(internal_conf)
        self.conf_paths = conf_paths
        self.model_paths = model_paths
        self.invocation_options = invocation_options
        self.loop = asyncio.get_event_loop()
        self.models: List[Model] = []
        self.failures: List[str] = []

        self.console_printer.print_magenta(ef.bold + 'Welcome to CSAOpt v{}\n\n'.format(__version__))

    def _get_instance_manager(self, context, conf, internal_conf) -> InstanceManager:
        if conf.get('remote.local_docker', False) is True:
            from .instancemanager.local import Local
            return Local(conf, internal_conf)

        if not internet_connectivity_available():
            raise AssertionError('Configured remote/cloud execution but internet connectivity unavailable.')

        cloud_platform = conf['remote.platform']
        if cloud_platform == 'aws':
            return AWSTools(conf, internal_conf)
        # elif cloud_platform == 'gcp' etc...
        # return GCPTools()
        else:
            raise AttributeError('Cloud platform ' + cloud_platform + ' unrecognized.')

    def duplicate_remote_configs(self, configs):
        for config in configs:
            if config.get('remote', None) is not None:
                remote_conf = config['remote']
                break
        else:
            raise AssertionError('No remote configuration found')

        for config in configs:
            config['remote'] = remote_conf

    async def _run_async(self, loop):
        printer = self.console_printer
        printer.print_with_spinner('Loading Config')
        try:
            configs = [get_configs(conf_path) for conf_path in self.conf_paths]
            self.duplicate_remote_configs(configs)

            internal_conf = self.invocation_options['internal_conf']

            ctx = Context(printer, configs, internal_conf)
        except Exception as e:
            printer.spinner_failure()
            self.failures.append('Error while loading config: ' + str(e))
            raise e
        printer.spinner_success()

        printer.print_with_spinner('Loading Models')
        for idx, model_path in enumerate(self.model_paths):
            configs[idx]['model']['path'] = model_path
            log.debug('Loading model {}'.format(model_path))
            loader = ModelLoader(configs[idx], internal_conf)
            self.models.insert(idx, loader.get_model())
            log.debug('Models loaded succesfully.')
        printer.spinner_success()

        # Get cloud config, create instance manager
        self.remote_config = configs[0]

        if self.remote_config.get('remote.local_docker', False):
            start_msg = 'Starting local instances with docker'
        else:
            start_msg = 'Starting instances on {}'.format(self.remote_config['remote.platform'].upper())

        printer.print_with_spinner(start_msg)
        await asyncio.sleep(0.8)

        with self._get_instance_manager(ctx, self.remote_config, internal_conf) as instancemanager:
            log.debug('Entered instancemanager block')
            printer.spinner_success()
            printer.print_with_spinner('Waiting for broker to come online')

            broker_instance, workers = instancemanager.get_running_instances()
            log.debug('Got running instances: {}, {}'.format(broker_instance, workers))
            if hasattr(instancemanager, 'broker_password'):
                # password is none for local deploys
                printer.println('Broker password (in case you intend to re-use instances): ' +
                                instancemanager.broker_password)

            await asyncio.sleep(5.0)

            queue_ids: List[str] = []
            for worker in workers:
                if 'queue_id' in worker.props:
                    queue_ids.append(worker.props['queue_id'])
            log.debug('Got queue IDs (a.k.a. active workers): {}'.format(queue_ids))

            assert len(queue_ids) > 0, 'There should be at least one worker running'

            redis_connect_timeout = configs[0].get('broker.connect_timeout',
                                                   internal_conf['broker.defaults.connect_timeout'])
            async with timeout(30) as async_timeout:
                while not async_timeout.expired:
                    try:
                        await asyncio.sleep(5)
                        broker: Broker = Broker(
                            host=str(broker_instance.public_ip),
                            port=broker_instance.port,
                            queue_ids=queue_ids,
                            socket_connect_timeout=redis_connect_timeout,
                            password=broker_instance.props.get('password', None))
                        printer.spinner_success()
                        break
                    except ConnectionError:
                        pass

            if async_timeout.expired:
                log.debug('Timeout while waiting for Broker')
                printer.spinner_failure()
                raise TimeoutError('Timed out waiting for broker to come online')

            jobmanager = JobManager(ctx, broker, self.models, configs)

            await asyncio.sleep(5)  # wait for redis to start

            printer.print_with_spinner("Waiting for workers to join")
            for worker_id in (await jobmanager.wait_for_worker_join()):
                printer.println('Worker {} joined'.format(worker_id))

            printer.spinner_success()
            printer.print_with_spinner('Deploying model')
            try:
                await jobmanager.deploy_model()
            except Exception:
                msg = 'An exception occured during model deployment.'
                log.exception(msg)
                printer.spinner_failure()
                self.failures.append(msg)
                return

            printer.spinner_success()

            await asyncio.sleep(0.8)

            printer.print_with_spinner('Running Simulated Annealing')

            await asyncio.sleep(1)
            # TODO: this needs timeouts
            jobs: List[Job] = await jobmanager.submit()

            await jobmanager.wait_for_results()
            printer.spinner_success()

            printer.print_with_spinner('Retrieving results')
            printer.spinner_success()

            printer.print_with_spinner('Scanning for best result')

            best_job, best_value, best_state = jobmanager.scan_for_best_result(jobs)

            # To improve testability
            self.best_state = best_state
            self.best_value = best_value

            printer.spinner_success()

            printer.println('Evaluated: {} State: {}'.format(best_value, best_state))

            for index, job in enumerate(jobs):
                config = configs[0] if len(configs) == 1 else configs[index]
                save_to_file = config.get('save_to_file.type', 'none')
                base_path = config.get('save_to_file.path', os.path.dirname(os.path.realpath(__file__)))
                conf_name = config.get('name', ('optimization_' + str(int(time.time()))))
                path = os.path.join(base_path, conf_name)

                pathlib.Path(base_path, conf_name).mkdir(parents=True, exist_ok=True)

                binary = config.get('save_to_file.binary', False)
                if save_to_file == 'all':
                    job.write_files(path, binary)
                elif save_to_file == 'best':
                    job.write_files(path, binary, only_best=True)

            if save_to_file != 'none':
                printer.println('Files have successfully been written.')

            printer.println('Waiting for instances to shutdown. This might take a long time. If you configured ' +
                            'files to be written to disk, they are now ready for your perusal.')

    def run(self) -> None:
        """

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_async(loop))
        loop.close()

        if self.failures:
            self.console_printer.println(fg.red + 'It seems there have been errors. 🌩')
        else:
            self.console_printer.println(fg.green + 'All done. ✨')

    def cancel(self) -> None:
        pass


class Context:
    def __init__(self, console_printer: ConsolePrinter, configs: ConfigTree, internal_config: ConfigTree) -> None:
        self.console_printer: ConsolePrinter = console_printer
        self.configs = configs
        self.internal_config = internal_config
