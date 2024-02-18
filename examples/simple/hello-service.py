#!/usr/bin/env python3
from gi.repository import Gio, GLib
from gdbus_util import DBusObject


DBUS_NAME = "org.example.Hello"


class HelloService(DBusObject):
    dbus_info = """
        <node>
            <interface name='org.example.Hello'>                
                <method name='SayHello'>
                    <arg name='name' direction='in' type='s'/>
                    <arg name='output' direction='out' type='s'/>
                </method>            
            </interface>
        </node>
        """

    dbus_path = "/org/example/Hello"

    def SayHello(self, name: str):
        return f"Hello, {name}!"


bus = Gio.bus_get_sync(Gio.BusType.SESSION)
Gio.bus_own_name_on_connection(bus, DBUS_NAME, 0, None, None)
service = HelloService(bus)
GLib.MainLoop().run()
