import pathlib

__all__ = ['compiler']

from typing import List


class BuildResult:
    def __init__(self, artifacts: List[pathlib.Path], errors: List[str]) -> None:
        self.artifacts = artifacts
        self.errors = errors

    def failed(self) -> bool:
        return self.errors is not None and len(self.errors) > 0
