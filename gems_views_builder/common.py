import logging
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000
LOG_FORMAT = "[%(asctime)s][%(levelname)s][%(context)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ContextFilter(logging.Filter):
    def __init__(self, context: str = "-") -> None:
        super().__init__()
        self.context = context

    def filter(self, record: logging.LogRecord) -> bool:
        record.context = self.context
        return True


class PipelineLogger:
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        console_output: bool = True,
    ) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        self._formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        self._default_context = "gems views builder"
        self._pipeline_handler: logging.FileHandler | None = None
        self._pipeline_log_path: Path | None = None

        if console_output and not self._has_named_handler("_gems_console_handler"):
            console_handler = logging.StreamHandler(sys.stdout)
            setattr(console_handler, "_gems_console_handler", True)
            self._prepare_handler(console_handler, self._default_context)
            self.logger.addHandler(console_handler)

    def _has_named_handler(self, attribute_name: str) -> bool:
        return any(getattr(handler, attribute_name, False) for handler in self.logger.handlers)

    def _prepare_handler(self, handler: logging.Handler, context: str) -> None:
        handler.setFormatter(self._formatter)
        handler.addFilter(ContextFilter(context))

    def _iter_context_filters(self) -> Iterator[ContextFilter]:
        for handler in self.logger.handlers:
            for flt in handler.filters:
                if isinstance(flt, ContextFilter):
                    yield flt

    @property
    def pipeline_log_path(self) -> Path | None:
        return self._pipeline_log_path

    def set_context(self, context: str) -> None:
        for flt in self._iter_context_filters():
            flt.context = context

    @contextmanager
    def use_context(self, context: str) -> Iterator[None]:
        previous_context = next(self._iter_context_filters(), ContextFilter(self._default_context)).context
        self.set_context(context)
        try:
            yield
        finally:
            self.set_context(previous_context)

    def configure_pipeline_run(self, input_data_path: Path) -> Path:
        self.close_pipeline_run()
        logs_dir = input_data_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        log_path = logs_dir / f"pipeline-{timestamp}.log"

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        setattr(file_handler, "_gems_pipeline_handler", True)
        self._prepare_handler(file_handler, self._default_context)
        self.logger.addHandler(file_handler)

        self._pipeline_handler = file_handler
        self._pipeline_log_path = log_path
        return log_path

    def close_pipeline_run(self) -> None:
        if self._pipeline_handler is None:
            return
        self.logger.removeHandler(self._pipeline_handler)
        self._pipeline_handler.close()
        self._pipeline_handler = None
        self._pipeline_log_path = None
        self.set_context(self._default_context)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def exception(self, msg: str) -> None:
        self.logger.exception(msg)


logger = PipelineLogger("gems_views_builder")
