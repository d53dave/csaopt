__all__ = ['modelcompiler', 'aws', 'msgqclient']

__version__ = '0.1.0'
__appname__ = 'CSAOpt: Cloud based, GPU accelerated Simulated Annealing'

import asyncio
import logging
import shutil
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job
from asyncio.selector_events import BaseSelectorEventLoop
from typing import Dict, Any, Optional, List
from sty import fg, ef, renderer, rs

from .msgqclient.client import QueueClient
from .model_loader.model_loader import ModelLoader
from .model import Model

logger = logging.getLogger('csaopt.Runner')
fg.set('csaopt_magenta', 'rgb', (199, 51, 147))


class ConsolePrinter:

    def __init__(self) -> None:
        self.termsize = shutil.get_terminal_size((80, 20))
        self.last_line: str = ''
        self.has_scheduled_print: bool = False
        self.print_job: Optional[Job] = None
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.spinner: List[str] = ['◣', '◤', '◥', '◢']

    def print(self, txt: str) -> None:
        self.last_line = txt
        sys.stdout.write(txt + rs.all)

    def print_magenta(self, txt: str) -> None:
        self.print(fg.csaopt_magenta + txt)

    def print_with_spinner(self, txt: str) -> None:
        # Check if log level > info, skip spinner if so
        # Truncate to console width to fit spinner
        if self.print_job is not None:
            self.print_job.cancel()

        self.print_job = self.scheduler.add_job(
            lambda: self.print(txt), 'interval', seconds=0.4)

    def last_line_succeeded(self) -> None:
        # If log level > info, just re-print with 'done.'
        # Truncate to console width to fit message
        pass

    def last_line_failed(self) -> None:
        # If log level > info, just re-print with 'failed.'
        # Truncate to console width to fit message
        pass


class Runner:
    def __init__(self, model_path: str, ctx_obj: Dict[str, Any]) -> None:
        self.console_printer = ConsolePrinter()
        self.console_printer.print_magenta(
            ef.bold + 'Welcome to CSAOpt v{}'.format(__version__))
        self.loop = asyncio.get_event_loop()

        # Get, build and validate Model
        # loader = ModelLoader({'model_path': model_path},
        #                     ctx_obj['internal_conf'])
        # self.model = loader.get_model()
        self.model = None

        # Get cloud config, create instance manager
        self.cloud_config: Dict[str, str] = {}

    def run(self) -> None:
        """
        
        """
        logger.debug('Running model {}'.format(self.model))
        
    async def go(self, loop: BaseSelectorEventLoop, model: Model, ctx: object):
        client = await QueueClient.create(loop, ctx.obj['internal_conf'])
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

    def wait_for_complete(self) -> None:
        pass
