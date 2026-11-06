import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(here, "lib", "libraven.so")
if os.path.exists(lib_path) and "RAVEN_LIBRARY" not in os.environ:
    os.environ["RAVEN_LIBRARY"] = lib_path

from .raven import *
