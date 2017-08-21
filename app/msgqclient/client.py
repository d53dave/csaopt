import zmq
import asyncio
from tornado.ioloop import IOLoop
import capnp
import os
from app.jobs import Job

CWD = os.path.dirname(__file__)
tidings_capnp = capnp.load(os.path.join(CWD, 'capnp/src/tidings.capnp'))
plumbing_capnp = capnp.load(os.path.join(CWD, 'capnp/src/plumbing.capnp'))


class QueueClient:
    def __init__(self, ioloop, host, port):
        self.ctx = zmq.asyncio.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect('{}:{}'.format(host, port))
        ioloop.spawn_callback(self._get_stats_loop)
        self.submitted = {}

    def _process_submit_answer(self, resp):
        message = plumbing_capnp.Plumbing.from_bytes_packed(resp[0])
        self.submitted[message.id] = message

    async def _send_request(self, message):
        await self.socket.send_multipart(message)
        return await self.socket.recv_multipart()

    async def _get_stats_loop(self):
        pass

    async def submit_job(self, job: Job):
        message = tidings_capnp.Tiding.new_message()  # TODO finish this
        resp = await self._send_request(message)
        return self._process_submit_answer(resp)

    def get_results(id):
        pass

