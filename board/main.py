import microcontroller

from uno import Uno_IR

from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.handlers.sequences import send_string

keyboard = Uno_IR()

from kmk.extensions.media_keys import MediaKeys
keyboard.extensions.append(MediaKeys())

keyboard.modules.append(Layers())

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

# uncomment for RGB
from kmk.extensions.RGB import RGB
rgb = RGB(pixel_pin=microcontroller.pin.GPIO4, num_pixels=1)
keyboard.extensions.append(rgb)

def hsvKeyFactory(h=None, s=None, v=None):
    newKey = KC.NO.clone()
    def hsvFunc(key, keyboard, *args):
        nonlocal h, s, v
        h = h if h is not None else rgb.hue
        s = s if s is not None else rgb.sat
        v = v if v is not None else rgb.val
        rgb.set_hsv_fill(h, s, v)
        rgb.show()
    newKey.after_press_handler(hsvFunc)
    return newKey
    

# uncomment for IR
from IRModule import IR_Handler
irHandler = IR_Handler()
keyboard.modules.append(irHandler)
irHandler.pin = microcontroller.pin.GPIO25
SEND_IR_CODE = irHandler.newIRKey
PLAGUEIS = send_string("Did you ever hear the tragedy of Darth Plagueis The Wise? I thought not. It's not a story the Jedi would tell you. It's a Sith legend. Darth Plagueis was a Dark Lord of the Sith, so powerful and so wise he could use the Force to influence the midichlorians to create life… He had such a knowledge of the dark side that he could even keep the ones he cared about from dying. The dark side of the Force is a pathway to many abilities some consider to be unnatural. He became so powerful… the only thing he was afraid of was losing his power, which eventually, of course, he did. Unfortunately, he taught his apprentice everything he knew, then his apprentice killed him in his sleep. Ironic. He could save others from death, but not himself.")
R = hsvKeyFactory(0)
G = hsvKeyFactory((255)//3)
B = hsvKeyFactory((255*2)//3)
irHandler.map = { # Note that transparent keys don't work on the mapping here, every layer just have a value.  transparent might have undefined behavior.
                 "00FFE01F": (KC.B, KC.B, KC.B, KC.B), # Layers 1, 2, 3, and 4 are all "B" for this beautiful example
                 "00FF609F": (PLAGUEIS, PLAGUEIS, PLAGUEIS, PLAGUEIS),
                 "00FF28D7": (KC.RGB_HUI, KC.RGB_HUI, KC.RGB_HUI, KC.RGB_HUI),
                 "00FF08F7": (KC.RGB_HUD, KC.RGB_HUD, KC.RGB_HUD, KC.RGB_HUD),
                 "00FFA857": (KC.RGB_SAI, KC.RGB_SAI, KC.RGB_SAI, KC.RGB_SAI),
                 "00FF8877": (KC.RGB_SAD, KC.RGB_SAD, KC.RGB_SAD, KC.RGB_SAD),
                 "00FF6897": (KC.RGB_VAI, KC.RGB_VAI, KC.RGB_VAI, KC.RGB_VAI),
                 "00FF48B7": (KC.RGB_VAD, KC.RGB_VAD, KC.RGB_VAD, KC.RGB_VAD),
                 "00FF3AC5": (KC.RGB_MODE_RAINBOW, KC.RGB_MODE_RAINBOW, KC.RGB_MODE_RAINBOW, KC.RGB_MODE_RAINBOW),
                 "00FFBA45": (KC.RGB_MODE_PLAIN, KC.RGB_MODE_PLAIN, KC.RGB_MODE_PLAIN, KC.RGB_MODE_PLAIN),
                 "00FFE817": (KC.RGB_ANI, KC.RGB_ANI, KC.RGB_ANI, KC.RGB_ANI),
                 "00FFC837": (KC.RGB_AND, KC.RGB_AND, KC.RGB_AND, KC.RGB_AND),
                 "00FF1AE5": (R, R, R, R),
                 "00FF9A65": (G, G, G, G),
                 "00FFA25D": (B, B, B, B),
                 "00FF30CF": (KC.VOLU, KC.VOLU, KC.VOLU, KC.VOLU),
                 "00FF10EF": (KC.VOLD, KC.VOLD, KC.VOLD, KC.VOLD),
                 "new": (SEND_IR_CODE, SEND_IR_CODE, SEND_IR_CODE, SEND_IR_CODE)
                }

# uncomment for Encoder
from kmk.modules.encoder import EncoderHandler
encoder_handler = EncoderHandler()
keyboard.modules.append(encoder_handler)
encoder_handler.pins = ((microcontroller.pin.GPIO3, microcontroller.pin.GPIO2, None, False),)

encoder_handler.map = [ # From what I saw in the code, kc.trns doesn't work well in layers on encoders.
                       ((KC.VOLD, KC.VOLU),(KC.VOLD, KC.VOLU),), # Layer 1
                       ((KC.VOLD, KC.VOLU),(KC.VOLD, KC.VOLU),), # Layer 2
                       ((KC.VOLD, KC.VOLU),(KC.VOLD, KC.VOLU),), # Layer 3
                       ((KC.VOLD, KC.VOLU),(KC.VOLD, KC.VOLU),), # Layer 4
                      ]

keyboard.debug_enabled = True

if __name__ == '__main__':
    keyboard.go()