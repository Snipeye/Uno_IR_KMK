import microcontroller
import pulseio
from supervisor import ticks_ms
from kmk.modules import Module
from kmk.kmktime import ticks_diff
from kmk.handlers.sequences import send_string
from kmk.keys import KC
from kmk.types import KeySequenceMeta

def decode(values, boundarySize = 50):
    if (len(values) == 0):
        return None
    if (len(values) <= 3): # if there are only 3 values, it's probably a "repeat" command.
        return "repeat"

    marks = []
    spaces = []
    for value in values[2:]:
        if (value > 0):
            marks.append(value)
        else:
            spaces.append(-value)

    marks.sort()
    spaces.sort()

    markBoundaries = []
    spaceBoundaries = []
    if (len(marks) > 0):
        for pMark, nMark in zip(marks[:-1], marks[1:]):
            if ((nMark - pMark) > boundarySize):
                markBoundaries.append(nMark)
    if (len(spaces) > 0):
        for pSpace, nSpace in zip(spaces[:-1], spaces[1:]):
            if ((nSpace - pSpace) > boundarySize):
                spaceBoundaries.append(nSpace)

    possibilities = (len(markBoundaries)+1)*(len(spaceBoundaries)+1)
    if (possibilities > 10): # > 16):
        return None # Give up.  This is too ugly a protocol.

    if (len(values) & 0x1): # if we have an odd number of values,
        # we can IGNORE the last mark IF there are not multiple mark timings.
        # if there ARE multiple mark timings... we have to assume it matters
        # and append a space (the smallest space)
        if (len(markBoundaries) != 0):
            values.append(spaces[0])
    encodedValues = []
    valuePairs = []

    for i in range(len(values[2:])//2):
        valuePairs.append((values[2+i*2], values[3+i*2]))

    for (m, s) in valuePairs:
        s = -s
        mi = 0
        si = 0
        for mb in markBoundaries:
            if (m >= mb):
                mi += 1
            else:
                break
        for sb in spaceBoundaries:
            if (s >= sb):
                si += 1
            else:
                break
        encodedValues.append(str(mi*len(markBoundaries) + si))

    outHex = hex(int("".join(encodedValues), possibilities)).upper()[2:]
    return outHex

# Here I'm shimming the pulseio class with a couple changes:
# 1) It doesn't just return a pulse time, it also returns whether or not the pulse was a mark or space
# (This works until the pulseio is paused or restarted or whatever, which I haven't implemented)
# 2) The way the library works, when started it'll always wait for the first non-idle pulse
# That's fine EXCEPT that my decode watches for a long space to mark the start of a signal
# This will normally happen after a transmission, but when it's just started it won't.
# So I've added a "previous value" placeholder to make this more convenient
class pulse:
    def __init__(self, pin: microcontroller.Pin, maxlen: int = 2, idle_state: bool = False):
        self._pulse = pulseio.PulseIn(pin, maxlen, idle_state)
        self.isMark = True
        self.prevValue = (30000, not self.isMark) # the previous value we return was a space of 30ms

        self.queueUs = 0
        self.queueUsLen = 0
    def popleft(self):
        self.prevValue = self[0]
        self._pulse.popleft()
        self.isMark = not self.isMark
        if (self.queueUsLen):
            self.queueUs -= self.prevValue[0]
            self.queueUsLen -= 1
        return self.prevValue
    def __len__(self):
        return len(self._pulse)
    def __getitem__(self, index: int):
        toReturn = self._pulse[index]
        markCopy = self.isMark
        if (index & (0x1)):
            markCopy = not markCopy
        return (toReturn, markCopy)
    def __bool__(self):
        return len(self)>0
    def isEnd(self):
        # We're defining the end of sequence as either:
        # (A) A long space (10ms+, but might need to drop this to ~5ms: I'd be worried about going lower)
        # or (B) A sorta-long space (2-3ms) followed by a sorta-long mark (2-3ms), as might happen
        # in a 20-bit worst-case sony message OR RC-6 which only has a signal-free time of 2.7ms
        # followed by a header of 2.7ms (at least, in spec... in practice might be more blank time)
        myLen = len(self)
        p0 = None if not myLen else self[0]
        return (
            (p0 is not None)
            and (not p0[1]) # if the pulse we're returning is a space
            and (
                (
                    p0[0] >= 10000 # the space is 10ms or longer, which should be enough to guarantee it's the end.  Might need to fiddle.
                ) or (
                    (p0[0] >= 2300) # and it's at least 2.3ms (settling on that because the space could be as little as 2.6ms, plus some margin for safety)
                    and (myLen > 1) # and there's another item in the queue
                    and (self[1][0] >= 2100) # and it's a header (at least 2.1ms, since minimum header is 2.4ms in sony or 2.6ms in RC6 which are our trouble protocols)
                )
            )
        )
    def isStart(self):
        # Either the previous value was a space of 10ms or longer, OR
        # the previous value was a space of 2.3ms or longer AND we now
        # have a mark of 2.1ms or longer.
        return (
            (len(self)) # We have an item to return
            and (not self.prevValue[1]) # previous item was a space
            and (
                (self.prevValue[0] >= 10000) # that space was 10ms or longer
                or (
                    (self.prevValue[0] >= 2300) # that space was 2.3ms or longer AND
                    and (self[0][0] >= 2100) # the value we have now is at least 2.1ms or longer
                )
            )
        )
    def queueMs(self): # might use this for timing functions to see how "far behind" we (VERY ROUGHLY) are
        # This won't account for whatever pulse we're currently recording and haven't reached the end of.
        totalMicros = self.queueUs
        lenNow = len(self)
        while (lenNow != self.queueUsLen):
            for i in range(self.queueUsLen, lenNow):
                totalMicros += self[i][0]
                self.queueUsLen += 1
            lenNow = len(self)
        return (totalMicros+500)//1000

# Singleton
class ir():
    def __init__(self, pin: microcontroller.Pin):
        self.events = []

        self._pulse = pulse(pin, maxlen=1000, idle_state=True)
        self.pulses = []
        self.pulsesStart = 0
        self.currentValue = None
        self.lastDecodeStartTicks = 0 # Naming is hard, didn't want to make it too long: this variable holds the tim when we STARTED receiving the most recent successfuly-decoded signal

    def decodeHandler(self):
        # move self.pulses and self.pulsesStart into a safe place so they can't get overwritten.
        # Decode the pulses to a value: update currentValue, lastDecodeStartTicks, and startTime (if necessary)
        # Emit value

        newVal = decode(self.pulses)
        self.lastDecodeStartTicks = self.pulsesStart

        newPress = False
        if (self.currentValue):
            if (newVal == "repeat" or newVal == self.currentValue):
                # it's the same value, no change
                pass
            else:
                # we had an old value, now we have a new value
                self.events.append(("release", self.currentValue))
                newPress = True
        else:
            # we did not have an old value, but we now have a value.
            newPress = True
        if (newPress):
            self.currentValue = newVal
            self.events.append(("press", self.currentValue))

        self.pulses = []

    def readPulses(self, ticksNow: int):
        while (self._pulse):
            # if, at any point, the current values would "expire" (took longer than 200ms to receive)
            # we need to make sure we restart the pulses list
            ticksThen = ticks_diff(ticksNow, self._pulse.queueMs()) if len(self._pulse) > 100 else ticksNow # if we have too much backed up, MOVE ON.
            if (ticks_diff(ticksThen, self.pulsesStart) > 200): # Greater than 200ms.  Discard current pulses, restart.
                self.pulses = []
            if (self._pulse.isStart()): # If we're currently on the start, we might have accidentally read an end in.  Start implies it's a mark.
                if (
                    (len(self.pulses)) # if we had pulses
                    and (self.pulses[-1] < 0) # and the last one was a space
                ):
                    self.pulses.pop(-1)
                if (len(self.pulses)):
                    self.decodeHandler() # should move the self.pulses to another place (to start decoding) and clear it for new entries
                self.pulsesStart = ticksThen #ticks_diff(ticksNow, self._pulse.queueMs()) # start the timer back when we would have received the start pulse... roughly. # Avoid calling queueMs again
                readPulse = self._pulse.popleft()
                self.pulses.append(readPulse[0]) # only care about the value, not the "isMark"
            elif (self._pulse.isEnd()): # Great, we're at the end of the sequence!  Move on to decode. Note that this implies the pulse[0] is a space.
                if (len(self.pulses)):
                    self.decodeHandler()
                self._pulse.popleft() # and clear out the useless space, the mark starts us off.
            else:
                readPulse = self._pulse.popleft()
                if (len(self.pulses)): # we only append if we've already started (and we only start at a "start") or else it'll be chaos.
                    self.pulses.append(readPulse[0] if readPulse[1] else -readPulse[0]) # write a + or - value to indicate mark or space.

    def buttonTimeout(self, ticksNow: int):
        # After we've serviced all the pulses, we need to see if the button has been released.
        # I'm giving it 300ms, which should be adequate: if we haven't received a new signal within 300
        # ms, the button wasn't being held.  Only matters if something is actively being held, though.
        if (self.currentValue):
            gap = ticks_diff(ticksNow, self.lastDecodeStartTicks)
            if (gap > 300):
                # Button released.
                # send release message
                self.events.append(("release", self.currentValue))
                self.currentValue = None

    def service(self):
        # As frequently as possible, we call the service routing so the
        # class can go through and try to update everything internally
        ticksNow = ticks_ms()
        self.readPulses(ticksNow) # Make sure we're keeping the queue for the pulseio module empty.
        self.buttonTimeout(ticksNow) # Monitor timer to see if the button is still being pressed or has been released

        newEvents = self.events
        self.events = []
        return newEvents


class IR_Handler(Module):
    def __init__(self):
        self.ir = None
        self.pin = None
        self.map = None
        self.newIRKey = send_string("New IR Code!")

    def on_runtime_enable(self, keyboard):
        return

    def on_runtime_disable(self, keyboard):
        return

    def during_bootup(self, keyboard):
        if self.pin:
            self.ir = ir(self.pin)

    def before_matrix_scan(self, keyboard):
        '''
        Return value will be injected as an extra matrix update
        '''
        if (self.ir is not None):
            events = self.ir.service()
            for event in events:
                ev, key = event
                which = None
                mapKeys = self.map.keys()
                if (key in mapKeys):
                    which = self.map[key]
                elif ("new" in mapKeys) and (key != "repeat"):
                    which = self.map["new"]
                if (which):
                    if (isinstance(key, str)):
                        seq = []
                        for char in key:
                            kc = getattr(KC, char.upper())
                            if char.isupper():
                                kc = KC.LSHIFT(kc)
                            seq.append(kc)
                        self.newIRKey.meta = KeySequenceMeta(seq)
                    layer_id = keyboard.active_layers[0]
                    if (ev == "release"):
                        keyboard.remove_key(which[layer_id])
                    else:
                        keyboard.add_key(which[layer_id])

        return keyboard

    def after_matrix_scan(self, keyboard):
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return
