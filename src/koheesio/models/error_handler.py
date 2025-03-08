from typing import ClassVar, Optional, Type
from abc import ABC
from enum import Enum

from koheesio import Step
from koheesio.models import Field

ExceptionType = Type[Exception]


class HandlerAction(str, Enum):
    """Enumerator of actions to take when an error is caught."""

    RAISE = "raise"
    WARN = "warn"
    IGNORE = "ignore"


class ErrorHandlerException(Exception):
    """Custom exception class for handling errors within the Handler."""


class BaseErrorHandler(Step, ABC):
    """Base class for error handlers.

    Error handlers are used to catch specific errors and handle them based on the
    action specified.
    """

    catch: ClassVar[list[ExceptionType]]
    error: Optional[Exception] = Field(default=None, description="The error that was caught")
    action: HandlerAction = HandlerAction.RAISE
    message: str = Field(default=None, description="The message to log when the error is caught.")

    class Output(Step.Output):
        """Output class for BaseErrorHandler"""

        is_handled: bool = Field(default=False, description="True if the error was handled, False otherwise")

    def can_handle(self, error: Exception) -> bool:
        """Checks if the handler can handle the given error."""
        return any(isinstance(error, _c) for _c in self.catch)

    def handle(self, error: Optional[Exception] = None) -> None:
        """Handles the given error based on the specified config."""
        self.error = error or self.error
        if self.error is None:
            raise RuntimeError("No error to handle.")

        if not self.can_handle(self.error):
            raise ErrorHandlerException(
                f"Handler can't handle error of type {type(self.error)}. Expected one of {self.catch}"
            )

        self.log.debug(self.error)
        self.execute()

        if self.action == HandlerAction.RAISE:
            self.log.error(self.message)
            raise self.error
        elif self.action == HandlerAction.WARN:
            self.log.warning(self.message)
        elif self.action == HandlerAction.IGNORE:
            pass
        else:
            raise ValueError(f"Invalid action: {self.action}")
