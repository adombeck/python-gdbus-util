#!/usr/bin/env python3

import random
import subprocess
import sys
import time
from pathlib import Path

from gi.repository import Gio, GLib

SCRIPT_DIR = Path(__file__).parent

TIMEOUT = 1
DBUS_NAME = "org.example.Sleeper"
DBUS_PATH = "/org/example/Sleeper"
DBUS_SUBOBJECT_PATH = "/org/example/Sleeper/Object"
DBUS_SUBOBJECT_INTERFACE = "org.example.Sleeper.Object"
UNIT_NAMES = []


def start_service():
    global UNIT_NAMES
    unit_name = f"sleeper-service-test-{random.randbytes(4).hex()}"
    UNIT_NAMES.append(unit_name)
    cmd = [
        "systemd-run",
        "--user",
        "--service-type=dbus",
        "--collect",
        f"--unit={unit_name}.service",
        f"--property=BusName={DBUS_NAME}",
        "python3",
        str(SCRIPT_DIR / "sleeper-service.py"),
        str(TIMEOUT),
    ]
    print(" ".join(cmd), file=sys.stderr)
    try:
        subprocess.check_call(cmd, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        # Print the log of the service
        subprocess.check_call([
            "journalctl",
            "--user",
            f"-u{unit_name}.service",
            "--no-pager",
            "--output=cat",
        ])
        raise

    # Continuously print the log of the service without the timestamp
    cmd = [
        "journalctl",
        "--user",
        "-f",
        f"-u{unit_name}.service",
        "--no-pager",
        "--output=cat",
    ]
    print(" ".join(cmd), file=sys.stderr)
    subprocess.Popen(cmd)


def teardown():
    for unit_name in UNIT_NAMES:
        is_active = (
            subprocess.run(
                [
                    "systemctl",
                    "--user",
                    "-q",
                    "is-active",
                    f"{unit_name}.service",
                ]
            ).returncode
            == 0
        )
        if is_active:
            subprocess.run(
                [
                    "systemctl",
                    "--user",
                    "stop",
                    f"{unit_name}.service",
                ]
            )


def list_connected_dbus_names(bus: Gio.DBusConnection):
    resp = bus.call_sync(
        bus_name="org.freedesktop.DBus",
        object_path="/org/freedesktop/DBus",
        interface_name="org.freedesktop.DBus",
        method_name="ListNames",
        parameters=None,
        reply_type=None,
        flags=Gio.DBusCallFlags.NONE,
        timeout_msec=-1,
        cancellable=None,
    )
    return resp.unpack()[0]


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


def call_sleep(bus: Gio.DBusConnection, object_path: str, interface: str, seconds: int):
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


def test_exit_on_idle():
    """Test that the service exits when idle for TIMEOUT seconds."""
    start_service()

    # Call keep alive to ensure that the service is running
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    send_keep_alive(bus, DBUS_PATH, DBUS_NAME)

    # Check that the service is running
    dbus_names = list_connected_dbus_names(bus)
    assert DBUS_NAME in dbus_names

    time.sleep(TIMEOUT + 1)

    # Check that the service is gone
    assert DBUS_NAME not in list_connected_dbus_names(bus)


def test_call_extends_timeout(object_path: str, interface: str):
    """Test that a call to the service extends the timeout."""
    start_service()

    # Call keep alive to ensure that the service is running
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    send_keep_alive(bus, object_path, interface)

    # Check that the service is running
    dbus_names = list_connected_dbus_names(bus)
    assert DBUS_NAME in dbus_names

    # Sleep for the first half of the timeout
    time.sleep(TIMEOUT // 2)

    # Send a keep alive to extend the timeout
    send_keep_alive(bus, object_path, interface)

    # Sleep for the second half of the timeout plus a little extra
    time.sleep(TIMEOUT // 2 + 1)

    # Check that the service is still running
    dbus_names = list_connected_dbus_names(bus)
    print(f"XXX {dbus_names}", file=sys.stderr)
    assert DBUS_NAME in dbus_names

    # Let the service exit on idle
    time.sleep(TIMEOUT + 1)

    # Check that the service is gone
    assert DBUS_NAME not in list_connected_dbus_names(bus)


def test_ongoing_call_avoids_exit_on_idle(object_path: str, interface: str):
    """Test that an ongoing call avoids the service exiting."""
    start_service()

    # Call keep alive to ensure that the service is running
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    send_keep_alive(bus, object_path, interface)

    # Check that the service is running
    dbus_names = list_connected_dbus_names(bus)
    assert DBUS_NAME in dbus_names

    # Let the service sleep for a little more than the timeout
    call_sleep(bus, object_path, interface, TIMEOUT + 1)

    # Check that the service is still running
    dbus_names = list_connected_dbus_names(bus)
    assert DBUS_NAME in dbus_names

    # Let the service exit on idle
    time.sleep(TIMEOUT + 1)

    # Check that the service is gone
    assert DBUS_NAME not in list_connected_dbus_names(bus)


try:
    test_exit_on_idle()
    test_call_extends_timeout(object_path=DBUS_PATH, interface=DBUS_NAME)
    test_call_extends_timeout(object_path=DBUS_SUBOBJECT_PATH,
                              interface=DBUS_SUBOBJECT_INTERFACE)
    test_ongoing_call_avoids_exit_on_idle(object_path=DBUS_PATH,
                                          interface=DBUS_NAME)
    test_ongoing_call_avoids_exit_on_idle(object_path=DBUS_SUBOBJECT_PATH,
                                          interface=DBUS_SUBOBJECT_INTERFACE)
finally:
    teardown()
