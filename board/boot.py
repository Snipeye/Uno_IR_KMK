import microcontroller
import digitalio
import storage

button = digitalio.DigitalInOut(microcontroller.pin.GPIO5)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

if (button.value):
    storage.disable_usb_drive()
else:
    storage.enable_usb_drive()
