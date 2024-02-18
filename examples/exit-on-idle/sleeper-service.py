#!/usr/bin/env python3
import logging
import sys
import time

from gi.repository import Gio
from gdbus_util import DBusObject, ExitOnIdleService


DBUS_NAME = "org.example.Sleeper"

if len(sys.argv) > 1:
    # In the test, we pass the timeout as the first argument
    TIMEOUT = int(sys.argv[1])
else:
    TIMEOUT = 30


class SleeperService(DBusObject, ExitOnIdleService):
    dbus_info = """
        <node>
            <interface name='org.example.Sleeper'>                
                <method name='KeepAlive'/>
                <method name='Sleep'>
                    <arg name='seconds' direction='in' type='u'/>                    
                </method>                
            </interface>
        </node>
        """

    dbus_path = "/org/example/Sleeper"

    def __init__(self, connection: Gio.DBusConnection, **kwargs):
        DBusObject.__init__(self, connection)
        ExitOnIdleService.__init__(self, connection, **kwargs)

    def KeepAlive(self):
        pass

    def Sleep(self, seconds: int):
        time.sleep(seconds)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bus = Gio.bus_get_sync(Gio.BusType.SESSION)
service = SleeperService(connection=bus, name=DBUS_NAME, timeout=TIMEOUT)
service.run()
