import os
import subprocess
import random
import sys
import time

from behave import given, when, then
from pathlib import Path

from gi.repository import Gio, GLib

# behave requires step_impl to be redefined, tell Ruff to ignore this
# ruff: noqa: F811

SCRIPT_DIR = Path(__file__).parent

sys.path.insert(0, os.path.join("..", SCRIPT_DIR))

from testutil import (start_service, is_service_active,  # noqa: E402
                      continuously_print_service_output)

SERVICES_DIR = SCRIPT_DIR / ".." / "services"
SLEEPER_SERVICE = SERVICES_DIR / "sleeper_service.py"

DBUS_NAME = "org.example.Sleeper"
DBUS_PATH = "/org/example/Sleeper"
DBUS_INTERFACE = "org.example.Sleeper"
DBUS_SUBOBJECT_PATH = "/org/example/Sleeper/Object"
DBUS_SUBOBJECT_INTERFACE = "org.example.Sleeper.Object"


# A definition of the context we pass between step implementations.
# This is not actually the class that behave passes to the step_impl
# functions, but pretending that it is provides code completion.
class TestContext:
    unit_name: str
    journalctl_process: subprocess.Popen


def start_sleep_service(unit_name: str, timeout: int) -> subprocess.Popen:
    return start_service(SLEEPER_SERVICE, DBUS_NAME, unit_name,
                         str(timeout))


def send_keep_alive(bus: Gio.DBusConnection, object_path: str, interface: str):
    bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=object_path,
        interface_name=interface,
        method_name="KeepAlive",
        parameters=None,
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )


def call_sleep(bus: Gio.DBusConnection, object_path: str, interface: str,
               seconds: int):
    bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=object_path,
        interface_name=interface,
        method_name="Sleep",
        parameters=GLib.Variant("(u)", (seconds,)),
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )


@given("sleeper-service is running with a {timeout:d} second idle timeout")
def step_impl(context: TestContext, timeout: int):
    unit_name = f"sleeper-service-test-{random.randbytes(4).hex()}"
    context.unit_name = unit_name
    start_sleep_service(unit_name, timeout)
    context.journalctl_process = continuously_print_service_output(unit_name)


@when("I wait for {seconds:f} seconds")
@when("I wait for another {seconds:f} seconds")
def step_impl(context: TestContext, seconds: float):
    time.sleep(seconds)


@then("sleeper-service should be running")
@then("sleeper-service should still be running")
def step_impl(context: TestContext):
    return is_service_active(context.unit_name) is True


@then("sleeper-service should not be running")
def step_impl(context: TestContext):
    return is_service_active(context.unit_name) is False


@when("I let the sleeper-service sleep for {seconds:d} seconds")
def step_impl(context, seconds: int):
    call_sleep(context.bus, DBUS_PATH, DBUS_INTERFACE, seconds)


@when("I let a sub-object of the sleeper-service sleep for {seconds:d} seconds")
def step_impl(context, seconds: int):
    call_sleep(context.bus, DBUS_SUBOBJECT_PATH, DBUS_SUBOBJECT_INTERFACE,
               seconds)


@when("I call a method of the sleeper-service")
def step_impl(context):
    send_keep_alive(context.bus, DBUS_PATH, DBUS_INTERFACE)


@when("I call a method of a sub-object of the sleeper-service")
def step_impl(context):
    send_keep_alive(context.bus, DBUS_SUBOBJECT_PATH, DBUS_SUBOBJECT_INTERFACE)
