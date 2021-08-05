from pubsub import pub
from rtmidi.midiutil import open_midioutput
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, CONTROL_CHANGE, PITCH_BEND

from BoardInteraction import BoardInteractor, Fingers
from ThreadExtension import StoppableThread


class BoardToMIDI(StoppableThread):
    def __init__(self, debug=1):
        self._debug = debug
        self.MODULE_IDENTIFIER = "BoardToMIDI"
        self._b = BoardInteractor()

        self._midiout, self._port_name = open_midioutput()

    def dpr(self, msg, l=1):
        if self._debug >= l:
            print(self.MODULE_IDENTIFIER + msg)

    def run(self):
        pub.subscribe(self.handleFingerConnection, 'FingerConnection')
        pub.subscribe(self.handleLGyroData, 'LGyro')
        pub.subscribe(self.handleRGyroData, 'RGyro')

        self._b.start()

        cmd = None
        while cmd is None:
            cmd = input("input q to quit:")

        self._b.stop()

    def handleFingerConnection(self, con, finger):
        self.dpr("finger, {}, {}".format(con, finger), l=2)

    def handleLGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        self.dpr("LG: {} {}, {} {}, {} {}".format(
            roll, rollChanged, pitch, pitchChanged, yaw, yawChanged), l=3)

    def handleRGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        self.dpr("RG: {} {}, {} {}, {} {}".format(
            roll, rollChanged, pitch, pitchChanged, yaw, yawChanged), l=3)

    def startNote(self, pitch=60, vel=112):
        self.dpr("starting note {}, {}".format(pitch, vel), l=2)
        self._midiout.send_message([NOTE_ON, pitch, vel])

    def stopNote(self, pitch=60):
        self.dpr("stopping note {}".format(pitch), l=2)
        self._midiout.send_message([NOTE_OFF, pitch, 0])

    def cc(self, cc=0, value=0):
        self.dpr("sending cc {}={}".format(cc, value), l=3)
        self._midiout.send_message([CONTROL_CHANGE, cc, value])

    def pb(self, value=8192):
        self.dpr("sending pb {}".format(value), l=3)
        self._midiout.send_message([PITCH_BEND, value & 0x7f, (value >> 7) & 0x7f])


class M1(BoardToMIDI):
    """
    Simplest implementation of Midi mapping
    R yaw is note
    R roll is bend
    R pitch is note velocity and also cc 22
    L pinch starts and stops
    All other things are midi cc's
    22: R pitch
    23: L yaw
    24: L roll
    25: L pitch
    TODO: Add toggles for other finger connections
    TODO: Also what are the commonly used ccs like mod wheel and expression pedal use those instead
    """

    def __init__(self, debug=1):
        super().__init__(debug=debug)
        self._noteval = 60
        self._notevelocity = 64
        self._currentlyOnNote = None

    def handleFingerConnection(self, con, finger):
        super().handleFingerConnection(con, finger)
        if finger == "LIT":
            if con:
                nv = self._noteval
                self.startNote(pitch=nv, vel=self._notevelocity)
                self._currentlyOnNote = nv
            else:
                if self._currentlyOnNote is not None:
                    self.stopNote(pitch=self._currentlyOnNote)
                    self._currentlyOnNote = None

    def handleLGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        super().handleLGyroData(roll, pitch, yaw, rollChanged, pitchChanged, yawChanged)
        if rollChanged:
            self.cc(24, int(roll*127))
        if pitchChanged:
            self.cc(25, int(pitch*127))
        if yawChanged:
            self.cc(23, int(yaw*127))

    def handleRGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        super().handleRGyroData(roll, pitch, yaw, rollChanged, pitchChanged, yawChanged)
        if rollChanged:
            self.pb(int((roll-0.5) * 2.0 * 8192.0 + 8192.0))
        if pitchChanged:
            self._notevelocity = int(127 * pitch)
        if yawChanged:
            self._noteval = self.getNoteValForYaw(yaw)

    def getNoteValForYaw(self, yaw):
        return int(yaw * 127)


if __name__ == "__main__":
    btm = M1(debug=3)
    btm.run()
