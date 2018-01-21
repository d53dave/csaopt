__all__ = ['modelcompiler', 'ansible', 'aws', 'msgqclient']

__version__ = '0.1.0'

import asyncio

from asyncio.selector_events import BaseSelectorEventLoop
from typing import Dict, Any

from msgqclient.client import QueueClient
from model_loader.model_loader import ModelLoader
from model import Model


class Runner:

    def __init__(self, model_path: str, ctx: Dict[str, Any]) -> None:
        self.loop = asyncio.get_event_loop()
        
        loader = ModelLoader({'model_path': model_path},
                             ctx.obj['internal_conf'])
        model = loader.get_model()

    def run(self) -> None:
        pass

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

    def wait_for_complete() -> None:
        pass
