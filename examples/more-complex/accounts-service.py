#!/usr/bin/env python3
import hashlib
import logging
import os
import time

from gi.repository import Gio
from gdbus_util import DBusObject, DBusError, ExitOnIdleService


TIMEOUT = 30
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
        self.Password = None
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


class AccountsService(DBusObject, ExitOnIdleService):
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

    def __init__(self, connection: Gio.DBusConnection, **kwargs):
        self.connection = connection
        DBusObject.__init__(self, connection)
        ExitOnIdleService.__init__(self, connection, **kwargs)
        self.users = []

    def GetUsers(self):
        return [user.Name for user in self.users]

    def CreateUser(self, name: str):
        user = User(self.connection, str(len(self.users)), name)
        user.exit_on_idle_service = self
        self.users.append(user)
        self.emit_signal(
            signal_name="UserAdded",
            parameters={"user": user.dbus_path},
        )
        return user.dbus_path

    def check_idle(self):
        for user in self.users:
            if not user.check_idle():
                return False

        return super().check_idle()


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bus = Gio.bus_get_sync(Gio.BusType.SESSION)
service = AccountsService(connection=bus, name=DBUS_NAME, timeout=TIMEOUT)
service.run()
