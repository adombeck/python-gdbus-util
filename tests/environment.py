import logging
import os
from pathlib import Path
import subprocess
import sys

from gi.repository import Gio

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, os.path.join(SCRIPT_DIR, "testutil"))

from testutil import is_service_active, stop_service  # noqa: E402

logging.basicConfig(level=logging.DEBUG)


# This is not actually the class that behave passes to the functions
# below, but pretending that it is provides code completion
class EnvironmentContext:
    bus: Gio.DBusConnection
    unit_name: str
    journalctl_process: subprocess.Popen


def before_scenario(context: EnvironmentContext, scenario):
    context.bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    context.unit_name = None
    context.journalctl_process = None


def after_scenario(context: EnvironmentContext, scenario):
    if context.unit_name and is_service_active(context.unit_name):
        stop_service(context.unit_name)

    if context.journalctl_process:
        context.journalctl_process.terminate()


###############################################
# Enable Debug-on-Error support as described in
# https://behave.readthedocs.io/en/stable/tutorial.html#debug-on-error-in-case-of-step-failures
###############################################

BEHAVE_DEBUG_ON_ERROR = False


def setup_debug_on_error(userdata):
    global BEHAVE_DEBUG_ON_ERROR  # noqa: PLW0603
    BEHAVE_DEBUG_ON_ERROR = userdata.getbool("BEHAVE_DEBUG_ON_ERROR")
