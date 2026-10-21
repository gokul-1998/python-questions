"""
common_start.py
Common starter utilities, thread-safe logging, and timing decorators
for Python Multithreading Interview Questions (Intermediate & Advanced).
"""

import concurrent.futures
import contextlib
import functools
import logging
import os
import queue
import random
import sys
import threading
import time
from typing import Any, Callable, TypeVar

# Configure thread-aware console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [%(threadName)-12s] | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MultithreadingPrep")

T = TypeVar("T")


def benchmark_threads(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to measure wall-clock execution time of multithreaded functions."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(f"Finished '{func.__name__}' in {elapsed:.4f}s")
    return wrapper


def runtime_concurrency_info() -> dict[str, Any]:
    """Returns Python runtime & GIL status information (supports Python 3.13/3.14+)."""
    gil_enabled = True
    if hasattr(sys, "_is_gil_enabled"):
        gil_enabled = sys._is_gil_enabled()
    return {
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "gil_enabled": gil_enabled,
        "switch_interval_sec": sys.getswitchinterval(),
    }


if __name__ == "__main__":
    logger.info(f"Runtime Environment: {runtime_concurrency_info()}")