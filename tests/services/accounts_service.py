#!/usr/bin/env python3
import hashlib
import logging
import os
import time

from gi.repository import Gio, GLib
from gdbus_util import DBusObject, DBusError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DBUS_NAME = "org.example.Accounts"


class PasswordTooShortError(DBusError):
    name = "org.example.Accounts.Error.PasswordTooShort"


class User(DBusObject):
    dbus_info = """
    <node>
        <interface name='org.example.Accounts.User'>
            <method name='SetPassword'>
                <arg name='password' direction='in' type='s'/>
            </method>            
            <property name='Id' type='s' access='read'/>
            <property name='Name' type='s' access='readwrite'/>
            <property name='Password' type='s' access='read'/>
        </interface>
    </node>
    """

    @property
    def dbus_path(self):
        return f"/org/example/Accounts/User/{self.Id}"

    def __init__(self, connection: Gio.DBusConnection, _id: str, name):
        self.Id = _id
        self.Name = name
        self.Password = ""
        super().__init__(connection=connection)

    def SetPassword(self, password: str):
        if len(password) < 8:
            raise PasswordTooShortError(
                "Password must be at least 8 characters long",
            )

        salt = os.urandom(32)
        _hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        self.Password = f"{salt.hex()}${_hash.hex()}"
        self.emit_properties_changed_signal(
            interface_name="org.example.Accounts.User",
            changed_properties={"Password": self.Password},
        )

    def Sleep(self, seconds: int):
        """Used for testing"""
        time.sleep(seconds)


class AccountsService(DBusObject):
    dbus_info = """
        <node>
            <interface name='org.example.Accounts'>                
                <method name='GetUsers'>
                    <arg name='Users' direction='out' type='as'/>
                </method>
                <method name='CreateUser'>
                    <arg name='name' direction='in' type='s'/>
                    <arg name='user' direction='out' type='o'/>
                </method>
                <signal name="UserAdded">
                    <arg type="o" name="user"/>
                </signal>
            </interface>
        </node>
        """

    dbus_path = "/org/example/Accounts"

    def __init__(self, connection: Gio.DBusConnection):
        self.connection = connection
        DBusObject.__init__(self, connection)
        self.users = []

    def GetUsers(self):
        return [user.Name for user in self.users]

    def CreateUser(self, name: str):
        user = User(self.connection, str(len(self.users)), name)
        self.users.append(user)
        self.emit_signal(
            signal_name="UserAdded",
            parameters={"user": user.dbus_path},
        )
        return user.dbus_path


def main():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    Gio.bus_own_name_on_connection(bus, DBUS_NAME, 0, None, None)
    AccountsService(bus)
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()