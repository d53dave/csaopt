import pathlib

__all__ = ['model_loader']

from typing import List


class ValidationError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class LoadResult:
    def __init__(self, artifacts: List[pathlib.Path], errors: List[str]) -> None:
        self.artifacts = artifacts
        self.errors = errors

    def failed(self) -> bool:
        return self.errors is not None and len(self.errors) > 0

    def __str__(self) -> str:
        failed_or_success = 'success' if not self.failed() else 'failed'
        results = 'artifacts={}'.format(self.artifacts) if not self.failed() else 'errors={}'.format(self.errors)
        return 'BuildResult [{}]: {}'.format(failed_or_success, results)
