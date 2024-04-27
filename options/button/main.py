# This example demonstrates how to use the button if that's all you've got - it has an IR demodulator built-in, but if you don't want to use it you can ignore it.
# This example also loads the macro to type from a text file named "macro.txt" so it doesn't have to be saved directly in this keymap

# We'll be referencing the make_key, send_string, and simple_key_sequence functions KMK provides.
from kmk.keys import make_key
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

# Here, we're loading the text from the "macro.txt" file into the key
fp = open("macro.txt", "r")
typeText = fp.read()
print("Loaded text to write:\n", typeText)
macroKey = send_string(typeText)

# And, just to spice things up, we'll make it so that the RGB LED chnages to blue while it types
def setColorKey(color):
    def setColorFunc(key, keyboard, *args, **kwargs):
        nonlocal color
        rgb.hue = color
        rgb.animation_mode = AnimationModes.STATIC
        rgb.animate()
    return make_key(on_press=setColorFunc)
myKey = simple_key_sequence((
    setColorKey((255*2)//3),
    macroKey,
    setColorKey(0),
))

# Here we define the keymap.  Since we're not using layers and there's only one button, the keymap is... pretty simple.
keyboard.keymap = [[myKey]]

# I've enabled debugging just 'cause it helps if something goes wrong, but you don't have to.
keyboard.debug_enabled = True

# This next line is how you tell it all to start, it's necessary.
if __name__ == '__main__':
    keyboard.go()
