# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Thread pools for building view configs and their aggregation steps concurrently.

Threads give real parallelism here: Polars releases the GIL while it executes a query, and the
query itself runs on Polars' own thread pool. Configured through environment variables:

- ``GVB_VIEW_CONFIG_WORKERS``: view configs built concurrently (default: all of them).
- ``GVB_MAX_WORKERS``: aggregation steps (time and scenario aggregations) run concurrently, shared
  by all view configs (default: ``min(8, cpu count)``).

Setting both to 1 runs everything serially, as the pipeline originally did.

View configs have their own pool, separate from the aggregation one: a view config waits on its
aggregation steps, and waiting on tasks from inside the same bounded pool could deadlock.
"""

import atexit
import logging
import os
from collections.abc import Callable
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from functools import cache
from typing import Any


class SerialExecutor(Executor):
    """Runs each task immediately in the calling thread."""

    def submit(self, fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Future[Any]:
        future: Future[Any] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as error:
            future.set_exception(error)
        return future


def configured_max_workers() -> int:
    return max(1, int(os.environ.get("GVB_MAX_WORKERS", min(8, os.cpu_count() or 1))))


def configured_view_config_workers(view_config_count: int) -> int:
    return max(1, int(os.environ.get("GVB_VIEW_CONFIG_WORKERS", view_config_count)))


@cache
def get_executor() -> Executor:
    """The aggregation-step executor: one for the whole run, created on first use, shut down at exit."""
    workers = configured_max_workers()
    if workers <= 1:
        logging.info("Aggregation steps run serially")
        return SerialExecutor()
    logging.info(f"Aggregation steps run on {workers} threads")
    executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="gvb-aggregation")
    atexit.register(executor.shutdown)
    return executor
