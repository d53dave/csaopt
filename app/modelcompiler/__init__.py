import pathlib

__all__ = ['modelcompiler']

from typing import List


class BuildResult:
    def __init__(self, artifacts: List[pathlib.Path], errors: List[str]) -> None:
        self.artifacts = artifacts
        self.errors = errors

    def failed(self) -> bool:
        return self.errors is not None and len(self.errors) > 0

    def __str__(self) -> str:
        failed_or_success = 'success' if not self.failed() else 'failed'
        results = 'artifacts={}'.format(self.artifacts) if not self.failed() else 'errors={}'.format(self.errors)
        return 'BuildResult [{}]: {}'.format(failed_or_success, results)
