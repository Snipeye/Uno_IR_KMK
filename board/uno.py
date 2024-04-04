import microcontroller

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner


class Uno_IR(KMKKeyboard):
    def __init__(self):
        # create and register the scanner
        self.matrix = KeysScanner(
            # require argument:
            pins=[microcontroller.pin.GPIO5],
            # optional arguments with defaults:
            value_when_pressed=False,
            pull=True,
            interval=0.005,  # Debounce time in floating point seconds
            max_events=64
        )