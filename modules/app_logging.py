"""Registro centralizado de errores para Streamlit Cloud y desarrollo local."""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    _CONFIGURED = True


def log_exception(logger_name: str, message: str, exc: BaseException | None = None) -> None:
    configure_logging()
    logger = logging.getLogger(logger_name)
    if exc is None:
        logger.error(message)
    else:
        logger.exception("%s: %s", message, exc)


class AppExceptionHook:
    """Registra excepciones que escapan del flujo normal de Streamlit."""

    def __call__(self, exception_type, exception, traceback) -> None:
        configure_logging()
        logging.getLogger("app.unhandled").error(
            "Excepción no controlada",
            exc_info=(exception_type, exception, traceback),
        )
        sys.__excepthook__(exception_type, exception, traceback)
