import logging
import socket
import asyncio
from typing import Callable, Set, Type, Tuple
from grpclib import GRPCError, Status
from grpclib.exceptions import StreamTerminatedError
from tenacity import (
    retry,
    wait_exponential,
    stop_any,
    stop_after_attempt,
    stop_after_delay,
    RetryCallState,
)

from nillion_client.errors import PartyError


def _invoke_with_retry(func: Callable) -> Callable:
    max_attempts: int = 10
    max_sleep_seconds: int = 5
    timeout_seconds: int = 60

    retryable_grpc_statuses: Set[Status] = {
        Status.DEADLINE_EXCEEDED,
        Status.RESOURCE_EXHAUSTED,
        Status.UNAVAILABLE,
        Status.DATA_LOSS,
    }
    retryable_exceptions: Tuple[Type[BaseException], ...] = (
        GRPCError,
        OSError,
        ConnectionError,
        TimeoutError,
        StreamTerminatedError,
        socket.timeout,
        asyncio.TimeoutError,
    )

    def is_retryable_exception(retry_state: RetryCallState) -> bool:
        if retry_state.outcome is None or retry_state.outcome.exception() is None:
            return False

        exception = retry_state.outcome.exception()

        if isinstance(exception, PartyError):
            exception = exception.__cause__

        if not isinstance(exception, retryable_exceptions):
            return False

        if isinstance(exception, GRPCError):
            return exception.status in retryable_grpc_statuses

        return True

    def log_error(retry_state: RetryCallState) -> None:
        exception = retry_state.outcome.exception() if retry_state.outcome else None
        attempt_number: int = retry_state.attempt_number
        sleep_time: float = retry_state.upcoming_sleep or 0.0
        function_name = retry_state.fn.__name__ if retry_state.fn else "<unknown>"
        logging.warning(
            f"Invocation of {function_name} failed with error: {exception}, "
            f"attempt: {attempt_number}, "
            f"sleep_time: {sleep_time}s, "
            f"timeout: {timeout_seconds}s"
        )

    return retry(
        wait=wait_exponential(max=max_sleep_seconds),
        stop=stop_any(
            stop_after_attempt(max_attempts), stop_after_delay(timeout_seconds)
        ),
        retry=is_retryable_exception,
        reraise=True,
        after=log_error,
    )(func)
