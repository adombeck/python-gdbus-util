#!/usr/bin/env python3
import logging
import sys
import time

from gi.repository import Gio
from gdbus_util import DBusObject, ExitOnIdleService


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


DBUS_NAME = "org.example.Sleeper"
DEFAULT_TIMEOUT = 30


class SleeperObject(DBusObject):

    dbus_info = """
        <node>
            <interface name='org.example.Sleeper.Object'>                
                <method name='KeepAlive'/>
                <method name='Sleep'>
                    <arg name='seconds' direction='in' type='u'/>                    
                </method>                
            </interface>
        </node>
        """

    dbus_path = "/org/example/Sleeper/Object"

    def KeepAlive(self):
        pass

    def Sleep(self, seconds: int):
        time.sleep(seconds)


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
        # Create the sub-object
        obj = SleeperObject(self.connection)
        obj.exit_on_idle_service = self
        self.objects = [obj]

    def KeepAlive(self):
        pass

    def Sleep(self, seconds: int):
        time.sleep(seconds)

    def check_idle(self) -> bool:
        if not super().check_idle():
            return False

        for obj in self.objects:
            if not obj.check_idle():
                return False

        return True


def main():
    if len(sys.argv) > 1:
        # In the test, we pass the timeout as the first argument
        timeout = int(sys.argv[1])
    else:
        timeout = DEFAULT_TIMEOUT

    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    service = SleeperService(connection=bus, name=DBUS_NAME, timeout=timeout)
    service.run()


if __name__ == "__main__":
    main()
