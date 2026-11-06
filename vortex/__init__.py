import contextlib
import importlib
from importlib import metadata

try:
    # Change here if project is renamed and does not equal the package name
    package_name = "tidalvortex"
    __version__ = metadata.version(package_name)
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


from .control import *
from .mini import mini, parse_mini
from .pattern import *
from .utils import *
from .vortex import *


@contextlib.contextmanager
def vortex_dsl():
    """
    Create a Vortex DSL context, with a default LinkClock and some functions for
    managing Streams

    Returns
    -------
    ModuleType
        Vortex DSL module

    """
    # Import DSL module and get variables
    mod = importlib.import_module("vortex.boot")
    locals = vars(mod)

    # Start clock
    clock = locals["_default_clock"]
    clock.start()

    yield mod

    # We're exiting context, so stop clock thread
    clock.stop()
