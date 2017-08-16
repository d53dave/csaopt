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

    

    def _uncompress_payload(self, compressed: bytes) -> Dict[str, object]:
        dctx = zstd.ZstdDecompressor()
        decompressed = dctx.decompress(compressed)
        return ujson.loads(decompressed)
