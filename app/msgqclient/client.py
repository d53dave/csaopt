import zmq
import asyncio
from tornado.ioloop import IOLoop
import capnp

CWD = os.path.dirname(__file__)
tidings_capnp = capnp.load(os.path.join(CWD, 'capnp/src/tidings.capnp'))
plumbing_capnp = capnp.load(os.path.join(CWD, 'capnp/src/plumbing.capnp'))

class QueueClient:
    def __init__(self, ioloop, host, port):
        self.ctx = zmq.asyncio.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect('{}:{}'.format(host, port))
        ioloop.spawn_callback(self._get_stats_loop)

    async def send_request(self, message):
        await self.socket.send_multipart(message)
        return await self.socket.recv_multipart()

    async def _get_stats_loop(self):
        pass