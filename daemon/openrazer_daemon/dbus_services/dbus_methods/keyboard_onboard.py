# SPDX-License-Identifier: GPL-2.0-or-later

from openrazer_daemon.dbus_services import endpoint


def _check_key(store, key, layer):
    if store not in range(1, 6):
        raise ValueError("store has to be between 1 and 5")
    if key not in range(1, 0x100):
        raise ValueError("key has to be between 1 and 255")
    if layer not in (0, 1):
        raise ValueError("layer has to be 0 (standard) or 1 (Hypershift)")


@endpoint('razer.device.onboard', 'getKeys', out_sig='ay')
def get_onboard_keys(self):
    """
    Get the ids of the keys that can be bound, as IBM key positions

    :return: Key ids
    :rtype: bytes
    """
    self.logger.debug("DBus call get_onboard_keys")

    return list(self.ONBOARD_KEYS)


@endpoint('razer.device.onboard', 'getKeyAction', in_sig='yyy', out_sig='ay')
def get_key_action(self, store, key, layer):
    """
    Get the action stored on the device for a key

    :param store: 1 = the live profile, 2-5 = onboard profiles
    :type store: int

    :param key: Key id
    :type key: int

    :param layer: 0 = standard, 1 = Hypershift
    :type layer: int

    :return: <type> <length> <data...>
    :rtype: bytes
    """
    self.logger.debug("DBus call get_key_action")

    _check_key(store, key, layer)

    driver_path = self.get_driver_path('key_action')

    # Another sysfs writer can change the selected key between the write and the read
    for _ in range(3):
        with open(driver_path, 'wb') as driver_file:
            driver_file.write(bytes((store, key, layer)))
        with open(driver_path, 'rb') as driver_file:
            reply = driver_file.read().ljust(10, b'\0')
        if reply[0] == store and reply[1] == key:
            break
    else:
        raise OSError("key_action kept returning another key")

    return list(reply[3:min(5 + reply[4], 10)])


@endpoint('razer.device.onboard', 'setKeyAction', in_sig='yyyay', byte_arrays=True)
def set_key_action(self, store, key, layer, action):
    """
    Store an action on the device for a key

    :param store: 1 = the live profile, 2-5 = onboard profiles
    :type store: int

    :param key: Key id
    :type key: int

    :param layer: 0 = standard, 1 = Hypershift
    :type layer: int

    :param action: <type> <length> <data...>, 2 to 7 bytes
    :type action: bytes
    """
    self.logger.debug("DBus call set_key_action")

    _check_key(store, key, layer)
    if len(action) not in range(2, 8):
        raise ValueError("action has to be between 2 and 7 bytes")

    driver_path = self.get_driver_path('key_action')

    with open(driver_path, 'wb') as driver_file:
        driver_file.write(bytes((store, key, layer)) + bytes(action))

    if self.DRIVER_MODE:
        self.logger.warning("Onboard key bindings only act in device mode; set driver_mode = False "
                            "under [Device:%s] in razer.conf to use them while the daemon runs", self.serial)
