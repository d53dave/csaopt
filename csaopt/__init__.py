__all__ = ['modelcompiler', 'aws', 'msgqclient']

__version__ = '0.1.0'
__appname__ = 'CSAOpt: Cloud based, GPU accelerated Simulated Annealing'

import asyncio
import logging
import shutil
import sys
import time
import subprocess
import unicodedata
import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job
from asyncio.selector_events import BaseSelectorEventLoop
from typing import Dict, Any, Optional, List
from sty import fg, ef, renderer, rs
from datetime import datetime

from .msgqclient.client import QueueClient
from .model_loader.model_loader import ModelLoader
from .model import Model
from .utils import get_configs
from .instancemanager.instancemanager import InstanceManager
from .instancemanager.awstools import AWSTools

logger = logging.getLogger('csaopt.Runner')
fg.set('csaopt_magenta', 'rgb', (199, 51, 147))



class ConsolePrinter:

    status_done = 'Done.'
    status_failed = 'Failed.'
    __ANSI_escape_re = re.compile(r'[\x1B|\x1b]\[[0-?]*[ -/]*[@-~]')

    def __init__(self, log_level='info') -> None:
        self.current_spinner_index = 0
        self.termsize = shutil.get_terminal_size((80, 20))
        self.last_line: str = ''
        self.has_scheduled_print: bool = False
        self.print_job: Optional[Job] = None
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.spinner: List[str] = ['◣', '◤', '◥', '◢']
        self.log_level = log_level
        _, columns = subprocess.check_output(['stty', 'size']).split()
        self.columns = int(columns) if int(columns) < 80 else 80

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

    def print(self, txt: str) -> None:
        self.current_spinner_index = (self.current_spinner_index + 1) % len(self.spinner)
        sys.stdout.write(txt + rs.all)
        sys.stdout.flush()
        self.last_line = txt
    
    def println(self, txt: str) -> None:
        self.print(txt + rs.all + '\n')

    def print_magenta(self, txt: str) -> None:
        self.print(fg.csaopt_magenta + txt)

    def print_with_spinner(self, txt: str) -> None:
        # Check if log level > info, skip spinner if so
        # Truncate to console width to fit spinner

        self.scheduler.remove_all_jobs()
        self.last_line = txt

        self.print_job = self.scheduler.add_job(
            lambda: self.print('\r' + ConsolePrinter._format_to_width(self.columns, txt, self.spinner[self.current_spinner_index] + '    ')),
            'interval', 
            seconds=0.42, 
            id='print_job', 
            max_instances=1, 
            next_run_time=datetime.now()) # run now once, then periodically

    def spinner_success(self) -> None:
        # If log level < warn, just re-print with 'Done.'
        # Truncate to console width to fit message
        if self.log_level == 'info':
            self.scheduler.remove_all_jobs()
            self.println(ConsolePrinter._format_to_width(
                    self.columns, self.last_line[0:len(self.last_line) - len(ConsolePrinter.status_done)], fg.green + ConsolePrinter.status_done))

    def spinner_failure(self) -> None:
        # If log level < warn, just re-print with 'Failed.'
        # Truncate to console width to fit message
        if self.log_level == 'info':
            self.scheduler.remove_all_jobs()
            self.println(ConsolePrinter._format_to_width(
                    self.columns, self.last_line[0:len(self.last_line) - len(ConsolePrinter.status_failed)], fg.red + ConsolePrinter.status_failed))



class Runner:
    def __init__(self, model_path: str, conf_path: str, invocation_options: Dict[str, Any]) -> None:
        self.console_printer = ConsolePrinter()
        self.conf_path = conf_path
        self.model_path = model_path
        self.invocation_options = invocation_options
        self.loop = asyncio.get_event_loop()
        self.model = None
        self.failures = None

        self.console_printer.print_magenta(
            ef.bold + 'Welcome to CSAOpt v{}\n\n'.format(__version__))

    def _get_instance_manager(self, context, conf, internal_conf) -> InstanceManager:
        cloud_platform = conf['cloud.platform']
        if cloud_platform == 'aws':
            return AWSTools(context, conf, internal_conf)
        # elif cloud_platform == 'gcp' etc...
            # return GCPTools()
        else:
            raise AttributeError('Cloud platform ' + cloud_platform + ' unrecognized.')

    async def _run_async(self, loop):
        self.console_printer.print_with_spinner('Loading Config')
        try:
            conf = get_configs(self.conf_path)
            internal_conf = self.invocation_options['internal_conf']
            ctx = Context(self.console_printer, conf, internal_conf)

        except:
            self.console_printer.spinner_failure()
            raise

        conf['model']['path'] = self.model_path
        self.console_printer.spinner_success()
        logger.debug('Running model {}'.format(self.model))
        self.console_printer.print_with_spinner('Loading Model')
        loader = ModelLoader(conf, internal_conf)
        self.model = loader.get_model()
        logger.debug('Model loaded succesfully.')
        self.console_printer.spinner_success()

        # Get cloud config, create instance manager
        self.cloud_config: Dict[str, str] = {}

        self.console_printer.print_with_spinner(
            'Starting instances on {}'.format(conf['cloud.platform'].upper()))
        # with self._get_instance_manager(ctx, conf, internal_conf) as instancemanager:
            # pass
        await asyncio.sleep(5)
        self.console_printer.spinner_success()

    def run(self) -> None:
        """
        
        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_async(loop))
        loop.close()

        if self.failures:
            self.console_printer.println(
                fg.red + 'It seems there have been errors. 🌩')
        else:
            self.console_printer.println(fg.green + 'All done. ✨')
        pass
        
        
    async def go(self, loop: BaseSelectorEventLoop, model: Model, click_ctx: Any):
        client = await QueueClient.create(loop, click_ctx.obj['internal_conf'])
        asyncio.Task(self.periodic(client))
        await client._consume()

    async def periodic(self, client: QueueClient):
        while True:
            print('periodic')
            await asyncio.sleep(1)
            # await client._send_one('csaopt.data.in.t', key='TheKey', value={
            #     u'a': [(1, 2, 3), True]
            # })

    def cancel(self) -> None:
        pass


class Context:

    def __init__(self, console_printer: ConsolePrinter, config, internal_config) -> None:
        self.console_printer: ConsolePrinter = console_printer
        self.config = config
        self.internal_config = internal_config
