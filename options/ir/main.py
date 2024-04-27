# This example demonstrates how to use the IR Demodulator - it has a slot for a button, but if you don't want to use it you can ignore it.
# This example is built around a random sony blu-ray player remote I had laying around, but should be easily adaptable to anything.

# We'll be referencing the make_key, send_string, and simple_key_sequence functions KMK provides.
from kmk.keys import make_key, KC
from kmk.handlers.sequences import send_string, simple_key_sequence

# We'll also be using the uno keyboard definition
from uno import Uno_IR
keyboard = Uno_IR()

# If you want volume up/down buttons, play/pase, you'll need media keys.
from kmk.extensions.media_keys import MediaKeys
keyboard.extensions.append(MediaKeys())

# We'll use the RGB LED to incidate stuff about what's going on
from kmk.extensions.rgb import RGB, AnimationModes
import microcontroller
rgb = RGB(pixel_pin=microcontroller.pin.GPIO4, num_pixels=1)
rgb.val = 10
keyboard.extensions.append(rgb)

# This example also shows how layers work
from kmk.modules.layers import Layers
keyboard.modules.append(Layers())

# The keymap for the button is very simple: it's just the letter A.  Feel free to adapt.
keyboard.keymap = [
    [
     KC.A
    ],
    [
     KC.TRNS
    ],
    [
     KC.TRNS
    ],
    [
     KC.TRNS
    ]
]

# We're going to set up everything so the RGB LED can work as a layer indicator
def layerFactory(hue=None, layer=None):
    def colorFunc(key, keyboard, *args, **kwargs):
        nonlocal hue
        rgb.hue = rgb.hue if hue is None else hue
    newKey = make_key(on_press=colorFunc)
    return simple_key_sequence((newKey, KC.RGB_MODE_RAINBOW if hue is None else KC.RGB_MODE_PLAIN, KC.TO(layer)))

# Now we'll build out the keys we'll use in the keymap
R0 = layerFactory(0, 0)
G1 = layerFactory(255//3, 1)
B2 = layerFactory((255*2)//3, 2)
Y3 = layerFactory(None, 3)

# A couple extra keys for special volume effects on MacOS
def addMods(key, keyboard, *args):
    keyboard.add_key(KC.LSFT)
    keyboard.add_key(KC.LALT)
def removeMods(key, keyboard, *args):
    keyboard.remove_key(KC.LSFT)
    keyboard.remove_key(KC.LALT)

SMALL_VOLU = KC.VOLU.clone()
SMALL_VOLU.before_press_handler(addMods)
SMALL_VOLU.after_release_handler(removeMods)
SMALL_VOLD = KC.VOLD.clone()
SMALL_VOLD.before_press_handler(addMods)
SMALL_VOLD.after_release_handler(removeMods)

# The IR Module below is what actually handles listening for codes and mapping them to functions.
from IRModule import IR_Handler
irHandler = IR_Handler()
keyboard.modules.append(irHandler)
irHandler.pin = microcontroller.pin.GPIO25
SEND_IR_CODE = irHandler.newIRKey

irHandler.map = { # Note that transparent keys don't work on the mapping here, every layer just have a value.  transparent might have undefined behavior.
                 "490": (KC.VOLU, SMALL_VOLU, KC.BRIGHTNESS_UP, SEND_IR_CODE),
                 "C90": (KC.VOLD, SMALL_VOLD, KC.BRIGHTNESS_DOWN, SEND_IR_CODE),
                 "E6B47": (R0, R0, R0, R0),
                 "16B47": (G1, G1, G1, G1),
                 "66B47": (B2, B2, B2, B2),
                 "96B47": (Y3, Y3, Y3, Y3),
                 "new": (KC.NO, KC.NO, KC.NO, SEND_IR_CODE), # When we get a new code, we DO want to print that out for programming (ONLY ON THE LAST LAYER) - comment this line if that's not true
                 "B47": (KC.N1, send_string("I"), send_string("one"), SEND_IR_CODE),
                 "80B47": (KC.N2, send_string("II"), send_string("two"), SEND_IR_CODE),
                 "40B47": (KC.N3, send_string("III"), send_string("three"), SEND_IR_CODE),
                 "C0B47": (KC.N4, send_string("IV"), send_string("four"), SEND_IR_CODE),
                 "20B47": (KC.N5, send_string("V"), send_string("five"), SEND_IR_CODE),
                 "A0B47": (KC.N6, send_string("VI"), send_string("six"), SEND_IR_CODE),
                 "60B47": (KC.N7, send_string("VII"), send_string("seven"), SEND_IR_CODE),
                 "E0B47": (KC.N8, send_string("VIII"), send_string("eight"), SEND_IR_CODE),
                 "10B47": (KC.N9, send_string("IX"), send_string("nine"), SEND_IR_CODE),
                 "90B47": (KC.N0, send_string("...0?"), send_string("zero"), SEND_IR_CODE),
}

keyboard.debug_enabled = True

if __name__ == '__main__':
    keyboard.go()
