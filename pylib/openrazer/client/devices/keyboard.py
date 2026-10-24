# SPDX-License-Identifier: GPL-2.0-or-later

"""
Contains functionality specific to keyboard-like devices
"""

from collections.abc import Iterable

import dbus as _dbus  # type: ignore

from openrazer.client.constants import MACRO_LED_STATIC, MACRO_LED_BLINK
from openrazer.client.devices import RazerDevice as __RazerDevice, BaseDeviceFactory as __BaseDeviceFactory


# Onboard key ids (IBM key positions) and the factory action of each, in hex, as read from a
# Huntsman V2. Position 59 is Fn (11 01 01): rebinding it loses the Fn layer.
ONBOARD_KEYS = {
    'grave': (1, '02020035'), '1': (2, '0202001e'), '2': (3, '0202001f'), '3': (4, '02020020'), '4': (5, '02020021'),
    '5': (6, '02020022'), '6': (7, '02020023'), '7': (8, '02020024'), '8': (9, '02020025'), '9': (10, '02020026'),
    '0': (11, '02020027'), 'minus': (12, '0202002d'), 'equal': (13, '0202002e'), 'yen': (14, '02020089'),
    'backspace': (15, '0202002a'), 'tab': (16, '0202002b'), 'q': (17, '02020014'), 'w': (18, '0202001a'),
    'e': (19, '02020008'), 'r': (20, '02020015'), 't': (21, '02020017'), 'y': (22, '0202001c'), 'u': (23, '02020018'),
    'i': (24, '0202000c'), 'o': (25, '02020012'), 'p': (26, '02020013'), 'leftbrace': (27, '0202002f'),
    'rightbrace': (28, '02020030'), 'backslash': (29, '02020031'), 'capslock': (30, '02020039'),
    'a': (31, '02020004'), 's': (32, '02020016'), 'd': (33, '02020007'), 'f': (34, '02020009'), 'g': (35, '0202000a'),
    'h': (36, '0202000b'), 'j': (37, '0202000d'), 'k': (38, '0202000e'), 'l': (39, '0202000f'),
    'semicolon': (40, '02020033'), 'apostrophe': (41, '02020034'), 'iso_hash': (42, '02020032'),
    'enter': (43, '02020028'), 'leftshift': (44, '02020200'), 'iso_backslash': (45, '02020064'),
    'z': (46, '0202001d'), 'x': (47, '0202001b'), 'c': (48, '02020006'), 'v': (49, '02020019'), 'b': (50, '02020005'),
    'n': (51, '02020011'), 'm': (52, '02020010'), 'comma': (53, '02020036'), 'dot': (54, '02020037'),
    'slash': (55, '02020038'), 'ro': (56, '02020087'), 'rightshift': (57, '02022000'), 'leftctrl': (58, '02020100'),
    'leftalt': (60, '02020400'), 'space': (61, '0202002c'), 'rightalt': (62, '02024000'),
    'rightctrl': (64, '02021000'), 'insert': (75, '02020049'), 'delete': (76, '0202004c'), 'left': (79, '02020050'),
    'home': (80, '0202004a'), 'end': (81, '0202004d'), 'up': (83, '02020052'), 'down': (84, '02020051'),
    'pageup': (85, '0202004b'), 'pagedown': (86, '0202004e'), 'right': (89, '0202004f'), 'numlock': (90, '02020053'),
    'kp7': (91, '0202005f'), 'kp4': (92, '0202005c'), 'kp1': (93, '02020059'), 'kpslash': (95, '02020054'),
    'kp8': (96, '02020060'), 'kp5': (97, '0202005d'), 'kp2': (98, '0202005a'), 'kp0': (99, '02020062'),
    'kpasterisk': (100, '02020055'), 'kp9': (101, '02020061'), 'kp6': (102, '0202005e'), 'kp3': (103, '0202005b'),
    'kpdot': (104, '02020063'), 'kpminus': (105, '02020056'), 'kpplus': (106, '02020057'),
    'kpcomma': (107, '02020085'), 'kpenter': (108, '02020058'), 'esc': (110, '02020029'), 'f1': (112, '0202003a'),
    'f2': (113, '0202003b'), 'f3': (114, '0202003c'), 'f4': (115, '0202003d'), 'f5': (116, '0202003e'),
    'f6': (117, '0202003f'), 'f7': (118, '02020040'), 'f8': (119, '02020041'), 'f9': (120, '02020042'),
    'f10': (121, '02020043'), 'f11': (122, '02020044'), 'f12': (123, '02020045'), 'sysrq': (124, '02020046'),
    'scrolllock': (125, '02020047'), 'pause': (126, '02020048'), 'leftmeta': (127, '02020800'),
    'compose': (129, '02020065'), 'muhenkan': (150, '0202008b'), 'katakanahiragana': (151, '02020088'),
    'hanja': (152, '02020091'), 'hangeul': (153, '02020090'), 'henkan': (154, '0202008a'),
    'mute': (200, '0a0200e2'), 'previoussong': (201, '0a0200b6'), 'nextsong': (202, '0a0200b5'),
    'volumeup': (204, '0a0200e9'), 'playpause': (205, '0a0200cd'), 'volumedown': (206, '0a0200ea'),
}


def onboard_macro_events(usages: Iterable[int], delay_ms: int = 10) -> bytes:
    """
    Build an onboard macro event stream that taps each key in turn

    :param usages: HID keyboard usages, e.g. (0x10, 0x12, 0x12) for "moo"
    :type usages: iterable of int

    :param delay_ms: Delay after each key down and key up, 0 to 255
    :type delay_ms: int

    :return: Events for add_onboard_macro
    :rtype: bytes
    """
    events = bytearray()
    for usage in usages:
        events += bytes((0x01, usage, 0x11, delay_ms, 0x02, usage, 0x11, delay_ms))
    return bytes(events)


class RazerKeyboard(__RazerDevice):
    @property
    def game_mode_led(self) -> bool:
        """
        Get game mode LED state

        :return: LED state
        :rtype: bool
        """
        if self.has('game_mode_led'):
            return bool(self._dbus_interfaces['game_mode_led'].getGameMode())
        else:
            raise NotImplementedError()

    @game_mode_led.setter
    def game_mode_led(self, value: bool) -> None:
        """
        Set game mode LED state

        :param value: LED State
        :type value: bool
        """
        if self.has('game_mode_led'):
            if value:
                self._dbus_interfaces['game_mode_led'].setGameMode(True)
            else:
                self._dbus_interfaces['game_mode_led'].setGameMode(False)
        else:
            raise NotImplementedError()

    @property
    def macro_mode_led(self) -> bool:
        """
        Get macro mode LED state

        :return: LED state
        :rtype: bool
        """
        if self.has('macro_mode_led'):
            return bool(self._dbus_interfaces['macro_mode_led'].getMacroMode())
        else:
            raise NotImplementedError()

    @macro_mode_led.setter
    def macro_mode_led(self, value: bool) -> None:
        """
        Set macro mode LED state

        :param value: LED State
        :type value: bool
        """
        if self.has('macro_mode_led'):
            if value:
                self._dbus_interfaces['macro_mode_led'].setMacroMode(True)
            else:
                self._dbus_interfaces['macro_mode_led'].setMacroMode(False)
        else:
            raise NotImplementedError()

    @property
    def macro_mode_led_effect(self) -> int:
        """
        Get macro mode LED effect

        Can get either blinking or static
        :return: Effect ID
        :rtype: int
        """
        if self.has('macro_mode_led_effect'):
            return int(self._dbus_interfaces['macro_mode_led'].getMacroEffect())
        else:
            raise NotImplementedError()

    @macro_mode_led_effect.setter
    def macro_mode_led_effect(self, value: int) -> None:
        """
        Set macro mode LED effect

        Can set to either MACRO_LED_STATIC or MACRO_LED_BLINK
        :param value: Effect ID
        :type value: int
        """
        if self.has('macro_mode_led_effect'):
            if value in (MACRO_LED_STATIC, MACRO_LED_BLINK):
                self._dbus_interfaces['macro_mode_led'].setMacroEffect(value)
            else:
                raise ValueError(f"Unexpected MACRO_LED_* value passed {value}")
        else:
            raise NotImplementedError()

    @property
    def keyswitch_optimization(self) -> bool:
        """
        Get keyswitch optimization state

        :return: Keyswitch optimization state
        :rtype: bool
        """
        if self.has('keyswitch_optimization'):
            return bool(self._dbus_interfaces['keyswitch_optimization'].getKeyswitchOptimization())
        else:
            raise NotImplementedError()

    @keyswitch_optimization.setter
    def keyswitch_optimization(self, value: bool) -> None:
        """
        Set keyswitch optimization state

        :param value: Keyswitch optimization state
        :type value: bool
        """
        if self.has('keyswitch_optimization'):
            self._dbus_interfaces['keyswitch_optimization'].setKeyswitchOptimization(value)
        else:
            raise NotImplementedError()

    @property
    def profile_led_red(self) -> bool:
        """
         Get red profile LED state

         :return: Red profile LED state
         :rtype: bool
         """
        if self.has('lighting_profile_led_red'):
            return bool(self._dbus_interfaces['profile_led'].getRedLED())
        else:
            raise NotImplementedError()

    @profile_led_red.setter
    def profile_led_red(self, enable: bool) -> None:
        """
        Set red profile LED state

        :param enable: Status of red profile LED
        :type enable: bool
        """
        if self.has('lighting_profile_led_red'):
            self._dbus_interfaces['profile_led'].setRedLED(enable)
        else:
            raise NotImplementedError()

    @property
    def profile_led_green(self) -> bool:
        """
        Get green profile LED state

        :return: Green profile LED state
        :rtype: bool
        """
        if self.has('lighting_profile_led_green'):
            return bool(self._dbus_interfaces['profile_led'].getGreenLED())
        else:
            raise NotImplementedError()

    @profile_led_green.setter
    def profile_led_green(self, enable: bool) -> None:
        """
        Set green profile LED state

        :param enable: Status of green profile LED
        :type enable: bool
        """
        if self.has('lighting_profile_led_green'):
            self._dbus_interfaces['profile_led'].setGreenLED(enable)
        else:
            raise NotImplementedError()

    @property
    def profile_led_blue(self) -> bool:
        """
        Get blue profile LED state

        :return: Blue profile LED state
        :rtype: bool
        """
        if self.has('lighting_profile_led_blue'):
            return bool(self._dbus_interfaces['profile_led'].getBlueLED())
        else:
            raise NotImplementedError()

    @profile_led_blue.setter
    def profile_led_blue(self, enable: bool) -> None:
        """
        Set blue profile LED state

        :param enable: Status of blue profile LED
        :type enable: bool
        """
        if self.has('lighting_profile_led_blue'):
            self._dbus_interfaces['profile_led'].setBlueLED(enable)
        else:
            raise NotImplementedError()

    def get_key_action(self, key: int, layer: int = 0, store: int = 1) -> bytes:
        """
        Get the action stored on the device for a key

        :param key: Key id, see ONBOARD_KEYS
        :type key: int

        :param layer: 0 = standard, 1 = Hypershift
        :type layer: int

        :param store: 1 = the live profile, 2-5 = onboard profiles
        :type store: int

        :return: <type> <length> <data...>
        :rtype: bytes

        :raises NotImplementedError: If function is not supported
        """
        if self.has('onboard_keys'):
            return bytes(self._dbus_interfaces['onboard'].getKeyAction(store, key, layer))
        else:
            raise NotImplementedError()

    def set_key_action(self, key: int, action: bytes, layer: int = 0, stores: tuple[int, ...] = (1,)) -> None:
        """
        Store an action on the device for a key

        :param key: Key id, see ONBOARD_KEYS
        :type key: int

        :param action: <type> <length> <data...>, 2 to 7 bytes
        :type action: bytes

        :param layer: 0 = standard, 1 = Hypershift
        :type layer: int

        :param stores: Stores to write, in order. Synapse writes only store 1 on keyboards.
        :type stores: tuple of int

        :raises NotImplementedError: If function is not supported
        """
        if self.has('onboard_keys'):
            for store in stores:
                self._dbus_interfaces['onboard'].setKeyAction(store, key, layer, _dbus.ByteArray(action))
        else:
            raise NotImplementedError()

    def set_key_remap(self, key: int, usage: int, modifiers: int = 0, layer: int = 0) -> None:
        """
        Make a key send another key

        :param key: Key id, see ONBOARD_KEYS
        :type key: int

        :param usage: HID keyboard usage, e.g. 0x04 for A
        :type usage: int

        :param modifiers: HID modifier bitmask, e.g. 0x01 for left Ctrl
        :type modifiers: int

        :param layer: 0 = standard, 1 = Hypershift
        :type layer: int
        """
        self.set_key_action(key, bytes((0x02, 0x02, modifiers, usage)), layer)

    def set_key_macro(self, key: int, macro_id: int, layer: int = 0) -> None:
        """
        Make a key play an onboard macro once

        :param key: Key id, see ONBOARD_KEYS
        :type key: int

        :param macro_id: Id of a macro added with add_onboard_macro
        :type macro_id: int

        :param layer: 0 = standard, 1 = Hypershift
        :type layer: int
        """
        self.set_key_action(key, bytes((0x03, 0x03)) + macro_id.to_bytes(2, 'big') + b'\x01', layer)

    def reset_key(self, name: str, layer: int = 0) -> None:
        """
        Give a key its factory action again. On layer 1 (Fn) this drops Fn functions such as the media keys.

        :param name: Key name from ONBOARD_KEYS, e.g. 'slash'
        :type name: str

        :param layer: 0 = standard, 1 = Hypershift
        :type layer: int
        """
        key, action = ONBOARD_KEYS[name]
        self.set_key_action(key, bytes.fromhex(action), layer)

    @property
    def onboard_macros(self) -> list[int]:
        """
        Get the ids of the macros in the device's memory

        :return: Macro ids
        :rtype: list of int

        :raises NotImplementedError: If function is not supported
        """
        if self.has('onboard_macros'):
            return [int(macro_id) for macro_id in self._dbus_interfaces['onboard'].getMacros()]
        else:
            raise NotImplementedError()

    @property
    def onboard_macro_storage(self) -> list[int]:
        """
        Get the device's macro memory usage

        :return: [max macros, total bytes, two device-specific fields]
        :rtype: list of int

        :raises NotImplementedError: If function is not supported
        """
        if self.has('onboard_macros'):
            return [int(value) for value in self._dbus_interfaces['onboard'].getMacroStorage()]
        else:
            raise NotImplementedError()

    def add_onboard_macro(self, macro_id: int, events: bytes) -> None:
        """
        Upload a macro to the device's memory

        :param macro_id: Macro id, 1 to 65535, not yet in use
        :type macro_id: int

        :param events: 0x01 <usage> key down, 0x02 <usage> key up, 0x11 <ms> and 0x12 <ms u16 BE> delays.
                       onboard_macro_events builds one.
        :type events: bytes

        :raises NotImplementedError: If function is not supported
        """
        if self.has('onboard_macros'):
            self._dbus_interfaces['onboard'].addMacro(macro_id, _dbus.ByteArray(events))
        else:
            raise NotImplementedError()

    def delete_onboard_macro(self, macro_id: int) -> None:
        """
        Delete a macro from the device's memory

        A key bound to a deleted macro does nothing, so this is refused while a key in store 1 still uses it.

        :param macro_id: Macro id
        :type macro_id: int

        :raises ValueError: If a key is still bound to the macro
        :raises NotImplementedError: If function is not supported
        """
        if self.has('onboard_macros') and self.has('onboard_keys'):
            bound = []
            for key in self._dbus_interfaces['onboard'].getKeys():
                for layer in (0, 1):
                    action = self.get_key_action(int(key), layer)
                    if action[0] == 0x03 and int.from_bytes(action[2:4], 'big') == macro_id:
                        bound.append("key {0} layer {1}".format(int(key), layer))
            if bound:
                raise ValueError("macro {0} is still bound to {1}".format(macro_id, ", ".join(bound)))
            self._dbus_interfaces['onboard'].deleteMacro(macro_id)
        else:
            raise NotImplementedError()
