.. toctree::
   :hidden:

   api/dbus_object
   api/exit_on_idle_service
   api/dbus_error

Python GDBus Util
=================

A collection of utilities to create GDBus services in Python.


DBusObject
----------

This class can be used to define a D-Bus object and register it on a
D-Bus connection.

See the :class:`~gdbus_util.DBusObject` documentation for more information.

ExitOnIdleService
-----------------

This class implements race-free exit-on-idle for a D-Bus service. It
is useful for services that are meant to be started on demand and exit
automatically when they are no longer needed.

See the :class:`~gdbus_util.ExitOnIdleService` documentation for more information.

Installation
------------

Install via pip:

.. code-block:: console

   $ pip install gdbus_util
