# This example demonstrates how to use the rotary encoder - it has an IR demodulator built-in, but if you don't want to use it you can ignore it.
# This example also loads an index of macros to type from a text file named "index.txt" so they don't have to be saved directly in this keymap

# We'll be referencing the make_key, send_string, and simple_key_sequence functions KMK provides.
from kmk.keys import make_key, KC
from kmk.handlers.sequences import send_string, simple_key_sequence
from kmk.types import KeySequenceMeta

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

# We'll declare the button that we'll use to print the macro so we can modify it
macroKey = send_string("")

# Here, we're loading the macro filenames from the "index.txt" file
fp = open("index.txt", "r")
macroTextFiles = list(fp.readlines())
macroTextFiles = [line.rstrip() for line in macroTextFiles] # Clean up trailing newlines
macroIndex = 0
loadedMacroIndex = -1
print("Loaded text filenames for macros:\n", macroTextFiles)
if (len(macroTextFiles) == 0):
    raise Exception("Cannot load any macros!")

# And write out the key/function we need to modify the macro key
def fileMacro(key, keyboard, *args, **kwargs):
    print("fileMacro called")
    global loadedMacroIndex
    if (loadedMacroIndex == macroIndex):
        # we're good, just type it
        pass
    else:
        fp = open(macroTextFiles[macroIndex], "r")
        toPrint = fp.read()
        # macroKey = send_string(toPrint)
        seq = []
        for char in toPrint:
            kc = getattr(KC, char.upper())
            if char.isupper():
                kc = KC.LSHIFT(kc)
            seq.append(kc)
        macroKey.meta = KeySequenceMeta(seq)
        print("Changed macroKey to print:")
        print(toPrint,"\n------\n")
        loadedMacroIndex = macroIndex
loadMacro = make_key(on_press=fileMacro)

# And, just to spice things up, we'll make it so that the RGB LED chnages to blue while it types
def setColorKey(color):
    def setColorFunc(key, keyboard, *args, **kwargs):
        nonlocal color
        rgb.hue = color
        rgb.animation_mode = AnimationModes.STATIC
        rgb.animate()
    return make_key(on_press=setColorFunc)
myKey = simple_key_sequence((
    setColorKey((255*2)//3), # Start by setting blue, to indicate we're active
    loadMacro, # make sure we have the right text loaded
    macroKey, # print it
    setColorKey(0), # return the LED to red
))

# We'll set up the encoder functions now that we've finished the button
from kmk.modules.encoder import EncoderHandler
encoder_handler = EncoderHandler()
encoder_handler.pins = ((microcontroller.pin.GPIO3, microcontroller.pin.GPIO2, None, False),)
keyboard.modules.append(encoder_handler)

def changeIndex(by):
    def changeIndexKey(key, keyboard, *args, **kwargs):
        nonlocal by
        global macroIndex
        macroIndex += by # increment/decrement
        macroIndex += len(macroTextFiles) # Make sure it's positive, not sure modulo works right on negative
        macroIndex %= len(macroTextFiles) # And keep it in range
    return make_key(on_press=changeIndexKey)

encoder_handler.map = [[[changeIndex(1), changeIndex(-1)]]]

# Note that the below code is just for "tap dance" - if you want an encoder-like experience but don't have an encoder, you can multiple-press the button to do the same thing.
"""
from kmk.modules.tapdance import TapDance
tapdance = TapDance()
tapdance.tap_time = 750
keyboard.modules.append(tapdance)
EXAMPLE_TD = KC.TD(
    myKey,
    changeIndex(1),
    changeIndex(-1),
)
# Here we define the keymap.
keyboard.keymap = [[EXAMPLE_TD]]
"""

# Here we define the keymap.  Since we're not using layers and there's only one button, the keymap is... pretty simple.
keyboard.keymap = [[myKey]]

# I've enabled debugging just 'cause it helps if something goes wrong, but you don't have to.
keyboard.debug_enabled = True

# This next line is how you tell it all to start, it's necessary.
if __name__ == '__main__':
    keyboard.go()
