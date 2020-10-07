"""
Simultaneous logging to file, console and Emme logbook using the root logger of the logging framework.

Also provides functionality for simultaneous file/console indent and Emme Logbook trace

Indent patterns and ideas based on the logging framework developed by Veitch Lister Consulting for zenith_model_run and
further adapted by Andrew O'Brien for the PTM

Initial Setup
-------------
>>> import logging
>>> import inro.emme.desktop.app as _app
>>> from four_step.common.logging_utils import logging_for_task, indent
>>>
>>> # can be called before connection to emme
>>> output_folder = 'path/to/schema/log'
>>> logging_for_task(output_folder)  # folder will be created if not exist
>>>
>>> model_app = _app.start_dedicated(visible=False, project='path/to/project/project.emp')
>>> # we can only add the emme handler after connection to the app
>>> add_emme_logging_handler()

Example
-------
>>> import logging
>>> from four_step.common.logging_utils import indent
>>>
>>> logging.info("message")
>>>
>>> with indent("block of work"):
>>>     logging.info("inside block")

Will output:
YYYY-MM-DD hh:mm:ss - PTM - INFO - message
YYYY-MM-DD hh:mm:ss - PTM - INFO - block of work
YYYY-MM-DD hh:mm:ss - PTM - INFO -   inside the block

Will also write the messages to the Emme Logbook, using trace blocks

Automatic Indenting of methods
------------------------------
>>> import logging
>>> from four_step.common.logging_utils import function_logging
>>>
>>> @function_logging("performing spam")
>>> def spam():
>>>     logging.info('in spam')
>>>
>>> spam()

Will output:
YYYY-MM-DD hh:mm:ss - PTM - INFO - performing spam
YYYY-MM-DD hh:mm:ss - PTM - INFO -   in spam
"""

from __future__ import print_function

import datetime
import inspect
import logging
import os
import os.path
import sys
from contextlib import contextmanager
from functools import wraps
from typing import Generator

from four_step.common.os_utils import startfile
from four_step.common.path_utils import mkdir_p

try:
    import inro.modeller as _m
except ImportError:
    logging.warn("Emme logging unavailable")

TEXT_LOG_FORMAT = "%(asctime)s - %(levelname)7s - %(indent_str)s%(message)s"
EMME_LOG_FORMAT = "%(message)s"  # basically a null format to keep emme log consistent
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
FORMATTER = logging.Formatter(TEXT_LOG_FORMAT, TIME_FORMAT)
INDENT_STR = "  "


class IndentingFilter(logging.Filter):
    """Add indents to the start of msg, depending on current indent level."""

    def __init__(self):
        """Create an indenting filter tracking the current indent level."""
        logging.Filter.__init__(self)
        self._indent = 0

    def filter(self, record):
        """Misuse the filter method to append an appropriate indent to the logging record."""
        record.indent_str = INDENT_STR * self._indent
        return True

    def increase_indent(self):
        """Increase the indent level."""
        self._indent += 1

    def decrease_indent(self):
        """Decrease the indent level."""
        self._indent -= 1


class EmmeHandler(logging.Handler):
    """Logging to the emme logbook."""

    def __init__(self):
        """Create a handler to manage python to logbook interactions."""
        logging.Handler.__init__(self)

    def handle(self, record):
        """Process the logging record."""

        # when we perform indenting, this allows us to avoid logging the indent message twice
        if not (hasattr(record, "skip_emme") and record.skip_emme):
            logging.Handler.handle(self, record)

    def emit(self, record):
        """Write the given record to the Emme logbook."""
        message = self.format(record)
        _m.logbook_write(message)


# Singleton module variables
# TODO: consider allowing indent to specify a new block name, or %(funcName)10.10s or %(fileName)10.10s
#       or pass an extra name: logging.info('message',extra={'stage': 'BaseNetwork'}) then use %(stage)10.10s
_indent_filter = IndentingFilter()
_use_emme = False
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.name = "StdOutHandler"


@contextmanager
def logging_for_task(output_folder, task_name, message=None, level=logging.INFO):
    # type: (str, str, str, int) -> Generator[None,None,None]
    """
    Set up logging for a specific task which should be logged in a separate file.

    Use this as soon as you have determined a suitable output_folder ie. before connecting to Emme
    Typically the path/to/horizon_year/log folder will be used.

    Will create output_folder if it does not exist.

    Will create the log file output_folder/YYYY-MM-DD_hhmmss_{task_name}.log

    Will NOT setup Emme logging - call add_emme_logging_handler() after _app.start_dedicated()

    After setup you can log using the standard Python logging framework

    Example
    -------
    >>> import logging
    >>> from four_step.common.logging_utils import logging_for_task
    >>>
    >>> output_folder = 'path/to/schema/log'
    >>> with logging_for_task(output_folder, "log_name"):
    >>>     logging.info('log message')
    >>>

    :param output_folder: typically path/to/schema/log
    :param task: task name to insert into filename
    :param level: the log level for all handlers
    :return: None
    """
    output_filename = get_output_filename(output_folder, task_name)

    root_logger = logging.getLogger()
    _ensure_indenting(root_logger)
    root_logger.setLevel(level)

    # Remove the existing file handlers on the root logger, store them for later restoration
    root_logger.info("Redirecting file based logging:")
    root_logger.info(" -> {}".format(output_filename))
    previous_level = root_logger.level
    existing_fh = [e for e in root_logger.handlers if isinstance(e, logging.FileHandler)]
    for fh in existing_fh:
        root_logger.removeHandler(fh)

    # add our new file handler with the task specific filename
    fh = logging.FileHandler(output_filename)
    fh.setLevel(level)
    fh.setFormatter(FORMATTER)
    root_logger.addHandler(fh)

    # Allow code execution to continue (potentially wrapping in an indent block)
    if message is not None:
        with indent(message):
            yield
    else:
        yield

    # Remove our new file handler and close it
    root_logger.removeHandler(fh)
    root_logger.setLevel(previous_level)
    fh.close()

    # Restore the previous file handlers
    for fh in existing_fh:
        root_logger.addHandler(fh)

    startfile(output_filename)


def basic_logging(level=logging.DEBUG):
    """Set up some basic logging to standard output."""
    logger = logging.getLogger()
    logger.setLevel(level)
    _ensure_stdout(logger, level)
    _ensure_indenting(logger)


def _ensure_indenting(logger):
    """Make sure that there our global indenting filter is attached to the root logger."""
    if _indent_filter not in logger.filters:
        logger.addFilter(_indent_filter)


def _ensure_stdout(logger, level):
    """Make sure that there our global stdout handler is attached to the root logger."""
    _stream_handler.setLevel(level)
    _stream_handler.setFormatter(FORMATTER)
    if "StdOutHandler" not in [e.name for e in logger.handlers]:
        logger.addHandler(_stream_handler)

    # Look for other stream handlers and remove them (Hack to get around double printing in Jupyter notebooks)
    for h in [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and h.name != "StdOutHandler"]:
        logger.removeHandler(h)


def add_emme_logging_handler(level=logging.DEBUG):
    """
    Add an Emme Logbook output Handler to the root logger.

    Also tells the indenting framework to start using logbook_trace.

    You must call this AFTER you have connected to the Emme app.

    >>> import inro.emme.desktop.app as _app
    >>> from four_step.common.logging_utils import logging_for_task
    >>>
    >>> model_app = _app.start_dedicated(visible=False, project='path/to/project/project.emp')
    >>> add_emme_logging_handler()

    :param level: the logging.level to use for the Emme Logbook output
    :return: None
    """
    logger = logging.getLogger()

    formatter = logging.Formatter(EMME_LOG_FORMAT, TIME_FORMAT)

    eh = EmmeHandler()
    eh.setLevel(level)
    eh.setFormatter(formatter)
    logger.addHandler(eh)

    global _use_emme
    _use_emme = True


def get_output_filename(output_folder, task):
    """Construct a dated filename in the given folder, creating it if required."""
    mkdir_p(output_folder)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return os.path.join(output_folder, "{}_{}.log".format(date_str, task))


@contextmanager
def indent(msg, format_kwargs_dict=None):
    """
    Context manager for increasing the indent and decreasing it after the block completes.

    Indents will be implemented in file and console using spaces
    Indents will be implemented in Emme Logbook using logbook_trace (if connected)

    msg will be passed through msg.format(**format_kwargs_dict)

    >>> import logging
    >>> from four_step.common.logging_utils import indent
    >>>
    >>> logging.info("message")
    >>>
    >>> with indent("block of {level} work", {'level': 'hard'}):
    >>>     logging.info("inside block")

    Will output:
    YYYY-MM-DD hh:mm:ss - PTM - INFO - message
    YYYY-MM-DD hh:mm:ss - PTM - INFO - block of hard work
    YYYY-MM-DD hh:mm:ss - PTM - INFO -   inside the block

    :param msg: message to log (at info level) to start the block
    :param format_kwargs_dict: dict to pass to msg.format(**format_kwargs_dict)
    :return: None
    """
    # TODO: we can probably get the caller the same as logging.findCaller
    format_kwargs_dict = format_kwargs_dict or {}
    formatted_msg = msg.format(**format_kwargs_dict)
    logging.info(formatted_msg, extra={"skip_emme": True})

    _indent_filter.increase_indent()
    try:
        if _use_emme:
            with _m.logbook_trace(formatted_msg):
                yield
        else:
            yield
    finally:
        _indent_filter.decrease_indent()


def function_logging(msg):
    """
    Automatically applies an indent block for all logging within a function.

    Designed to be used as a function decorator. This saves a level of code indentation when you want to log indent
    all the logging inside a method.

    The top level message message given will be output after interpolating with the function arguments.
    i.e. msg_actually_output = msg.format(**function_arguments_dictionary)
    This can be seen in the following example, where the string refers to the arg1 that is passed at runtime.

    >>> import logging
    >>> from four_step.common.logging_utils import function_logging
    >>>
    >>> @function_logging('performing spam and {arg1}')
    >>> def spam(arg1):
    >>>     logging.info('in spam')
    >>>
    >>> spam('ham')

    Will output:
    YYYY-MM-DD hh:mm:ss - PTM - INFO - performing spam and ham
    YYYY-MM-DD hh:mm:ss - PTM - INFO -   in spam

    :param msg: message to log (at info level) to start the block
    :return:
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            # format all arguments into a dictionary by argument name, including default arguments
            args_dict = inspect.getcallargs(function, *args, **kwargs)
            with indent(msg, args_dict):
                return function(*args, **kwargs)

        return wrapper

    return decorator