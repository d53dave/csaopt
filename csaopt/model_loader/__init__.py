"""
This module offers functionality regarding the loading and validation of optimiztion models.
"""

__all__ = ['model_loader', 'model_validator']


class ValidationError(Exception):
    """Exception class for function validation errors

    Args:
        message: Error message
    """

    def __init__(self, message: str) -> None:
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
