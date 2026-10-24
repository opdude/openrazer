# SPDX-License-Identifier: GPL-2.0-or-later

from openrazer_daemon.dbus_services import endpoint


@endpoint('razer.device.onboard', 'addMacro', in_sig='qay', byte_arrays=True)
def add_onboard_macro(self, macro_id, events):
    """
    Upload a macro to the device's memory

    Deleted macros keep their space until the device reclaims it, so prefer reusing ids.

    :param macro_id: Macro id, 1 to 65535, not yet in use
    :type macro_id: int

    :param events: Event stream: 0x01 <usage> key down, 0x02 <usage> key up, 0x11 <ms> and 0x12 <ms u16 BE> delays
    :type events: bytes
    """
    self.logger.debug("DBus call add_onboard_macro")

    if macro_id not in range(1, 0x10000):
        raise ValueError("macro_id has to be between 1 and 65535")
    if len(events) not in range(1, 4095):
        raise ValueError("events have to be between 1 and 4094 bytes")

    driver_path = self.get_driver_path('macro')

    with open(driver_path, 'wb') as driver_file:
        driver_file.write(macro_id.to_bytes(2, 'big') + bytes(events))


@endpoint('razer.device.onboard', 'deleteMacro', in_sig='q')
def delete_onboard_macro(self, macro_id):
    """
    Delete a macro from the device's memory

    Keys and buttons bound to the macro keep the binding; the client library checks for them first.

    :param macro_id: Macro id
    :type macro_id: int
    """
    self.logger.debug("DBus call delete_onboard_macro")

    driver_path = self.get_driver_path('macro_delete')

    with open(driver_path, 'w') as driver_file:
        driver_file.write(str(int(macro_id)))


@endpoint('razer.device.onboard', 'getMacros', out_sig='aq')
def get_onboard_macros(self):
    """
    Get the ids of the macros in the device's memory

    After a delete the Naga V2 Pro can leave live ids out of this list.

    :return: Macro ids
    :rtype: list of int
    """
    self.logger.debug("DBus call get_onboard_macros")

    driver_path = self.get_driver_path('macro_list')

    with open(driver_path, 'rb') as driver_file:
        data = driver_file.read()

    return [int.from_bytes(data[i:i + 2], 'big') for i in range(0, len(data) - 1, 2)]


@endpoint('razer.device.onboard', 'getMacroStorage', out_sig='au')
def get_onboard_macro_storage(self):
    """
    Get the device's macro memory usage

    :return: [max macros, total bytes, two device-specific fields]. On the Naga V2 Pro they are free and deleted bytes.
    :rtype: list of int
    """
    self.logger.debug("DBus call get_onboard_macro_storage")

    driver_path = self.get_driver_path('macro_storage')

    with open(driver_path, 'r') as driver_file:
        return [int(value) for value in driver_file.read().split()]
