import uuid
import zstdandard as zstd
import ujson

from Typing import Dict
from Typing import object

__all__ = ['jobmanager']


class Job():
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.expected_responses = []
        self.payload = None

    def finished(self):
        return self.payload is not None

    def _uncompress_payload(self, compressed: bytes) -> Dict[str, object]:
        """The message payload is a zstd compressed json string. Using zstandard and ujson to process"""
        dctx = zstd.ZstdDecompressor()
        decompressed = dctx.decompress(compressed)
        return ujson.loads(decompressed)


class SubmissionResult():
    def __init__(self, jobId, error):
        self.error = error
        self.jobId = jobId

    def failed(self) -> bool:
        return self.error is not None
