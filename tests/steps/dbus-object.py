import logging
import os
import subprocess
import random
import sys

from behave import given, when, then
from pathlib import Path

from gi.repository import Gio, GLib

# behave requires step_impl to be redefined, tell Ruff to ignore this
# ruff: noqa: F811

SCRIPT_DIR = Path(__file__).parent

sys.path.insert(0, os.path.join("..", SCRIPT_DIR))

from testutil import (start_service,  # noqa: E402
                      continuously_print_service_output)

from services.accounts_service import PasswordTooShortError  # noqa: E402

SERVICES_DIR = SCRIPT_DIR / ".." / "services"
ACCOUNTS_SERVICE = SERVICES_DIR / "accounts_service.py"

DBUS_NAME = "org.example.Accounts"
DBUS_PATH = "/org/example/Accounts"
DBUS_INTERFACE = "org.example.Accounts"
DBUS_USER_PATH = "/org/example/Accounts/User"
DBUS_USER_INTERFACE = "org.example.Accounts.User"

mainloop = GLib.MainLoop()
received_user_added_signal = False
received_properties_changed_signal = False

logger = logging.getLogger(__name__)


# A definition of the context we pass between step implementations.
# This is not actually the class that behave passes to the step_impl
# functions, but pretending that it is provides code completion.
class TestContext:
    bus: Gio.DBusConnection
    proxy: Gio.DBusProxy
    unit_name: str
    journalctl_process: subprocess.Popen
    user_path: str
    received_expected_error: bool


def start_accounts_service(unit_name: str) -> subprocess.Popen:
    return start_service(ACCOUNTS_SERVICE, DBUS_NAME, unit_name)


def call_set_password(context, password: str):
    context.bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=context.user_path,
        interface_name=DBUS_USER_INTERFACE,
        method_name="SetPassword",
        parameters=GLib.Variant("(s)", (password,)),
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )


def on_user_added_signal(connection: Gio.DBusConnection, sender_name: str,
                         object_path: str, interface_name: str, signal_name: str,
                         parameters: GLib.Variant):
    logger.debug("Received signal %s from %s", signal_name, sender_name)
    if signal_name == "UserAdded":
        logger.debug("Received UserAdded signal (parameters: %s)", parameters)
        global received_user_added_signal
        received_user_added_signal = True
        mainloop.quit()


def on_properties_changed(proxy: Gio.DBusProxy,
                          changed_properties: GLib.Variant,
                          invalidated_properties: GLib.Variant):
    logger.debug("Received PropertiesChanged signal "
                 "(changed_properties: %s, invalidated_properties: %s)")
    assert "Password" in changed_properties.unpack()
    global received_properties_changed_signal
    received_properties_changed_signal = True
    mainloop.quit()


@given("The accounts-service is running")
def step_impl(context):
    unit_name = f"accounts-service-test-{random.randbytes(4).hex()}"
    context.unit_name = unit_name
    start_accounts_service(unit_name)
    context.journalctl_process = continuously_print_service_output(unit_name)


@when("I subscribe to the UserAdded signal")
def step_impl(context):
    context.bus.signal_subscribe(
        sender=DBUS_NAME,
        interface_name=DBUS_INTERFACE,
        member="UserAdded",
        object_path=DBUS_PATH,
        arg0=None,
        flags=Gio.DBusSignalFlags.NONE,
        callback=on_user_added_signal,
    )


@then("I should receive the UserAdded signal")
def step_impl(context):
    mainloop.run()
    assert received_user_added_signal


@when("I call the CreateUser method")
def step_impl(context):
    user_path = context.bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=DBUS_PATH,
        interface_name=DBUS_INTERFACE,
        method_name="CreateUser",
        parameters=GLib.Variant("(s)", ("foo",)),
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )
    context.user_path = user_path.unpack()[0]


@when("I subscribe to the PropertiesChanged signal")
def step_impl(context):
    logger.debug("Subscribing to PropertiesChanged signal on %s", context.user_path)
    context.proxy = Gio.DBusProxy.new_sync(
        context.bus,
        Gio.DBusProxyFlags.NONE,
        None,
        DBUS_NAME,
        context.user_path,
        DBUS_USER_INTERFACE,
        None,
    )
    context.proxy.connect("g-properties-changed", on_properties_changed)


@when("I call the SetPassword method")
def step_impl(context):
    call_set_password(context, "securepassword")


@then("I should receive the PropertiesChanged signal")
def step_impl(context):
    mainloop.run()
    assert received_properties_changed_signal


@when("I call the SetPassword method with a password that is too short")
def step_impl(context):
    try:
        call_set_password(context, "short")
    except GLib.Error as e:
        assert PasswordTooShortError.is_instance(e)
        PasswordTooShortError.strip_remote_error(e)
        logger.info("Received expected error: %s", e)
        context.received_expected_error = True


@then("I should receive an error")
def step_impl(context):
    assert context.received_expected_error


@then("I should be able to read the {property_name} property of the user")
def step_impl(context, property_name: str):
    # Call the org.freedesktop.DBus.Properties.Get method
    result = context.bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=context.user_path,
        interface_name="org.freedesktop.DBus.Properties",
        method_name="Get",
        parameters=GLib.Variant("(ss)", (DBUS_USER_INTERFACE, property_name)),
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )
    assert result.unpack()[0] is not None


@then("I should be able to write the {property_name} property of the user")
def step_impl(context, property_name: str):
    # Call the org.freedesktop.DBus.Properties.Set method
    parameters = GLib.Variant("(ssv)", (
        DBUS_USER_INTERFACE, property_name, GLib.Variant("s", "newvalue"),
    ))
    context.bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=context.user_path,
        interface_name="org.freedesktop.DBus.Properties",
        method_name="Set",
        parameters=parameters,
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )
    # Check that the property has been updated
    result = context.bus.call_sync(
        bus_name=DBUS_NAME,
        object_path=context.user_path,
        interface_name="org.freedesktop.DBus.Properties",
        method_name="Get",
        parameters=GLib.Variant("(ss)", (DBUS_USER_INTERFACE, property_name)),
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )
    assert result.unpack()[0] == "newvalue"
