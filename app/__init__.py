__all__ = ['modelcompiler', 'aws', 'msgqclient']

__version__ = '0.1.0'
__appname__ = 'CSAOpt: Cloud based, GPU accelerated Simulated Annealing'

import asyncio
import logging
import shutil

from asyncio.selector_events import BaseSelectorEventLoop
from typing import Dict, Any
from sty import fg, ef, render, rs

from .msgqclient.client import QueueClient
from .model_loader.model_loader import ModelLoader
from .model import Model

logger = logging.getLogger('csaopt.Runner')
fg.csaopt_magenta = render.rgb_fg(199, 51, 147)


class ConsolePrinter:

    def __init__(self) -> None:
        self.termsize = shutil.get_terminal_size((80, 20))
        self.last_line = ''

    def print(self, txt: str) -> None:
        self.last_line = txt

    def print_magenta(self, txt: str) -> None:
        self.print(fg.csaopt_magenta + txt + rs.all)

    def print_with_spinner(self, txt: str) -> None:
        # Check if log level > info, skip spinner if so
        # Truncate to console width to fit spinner
        pass

    def last_line_succeeded(self) -> None:
        # If log level > info, just re-print with 'done.'
        # Truncate to console width to fit message
        pass

    def last_line_failed(self) -> None:
        # If log level > info, just re-print with 'failed.'
        # Truncate to console width to fit message
        pass


class Runner:
    def __init__(self, model_path: str, ctx: Dict[str, Any]) -> None:
        self.console_printer = ConsolePrinter()
        self.console_printer.print_magenta(
            ef.bold + 'Welcome to CSAOpt v{}'.format(__version__))
        self.loop = asyncio.get_event_loop()

        # Get, build and validate Model
        loader = ModelLoader({'model_path': model_path},
                             ctx.obj['internal_conf'])
        self.model = loader.get_model()

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
