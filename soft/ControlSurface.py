from PyQt5.QtWidgets import QLabel
from MIDI import MIDIMapping
import live


class C1Control:
    def __init__(self):
        self.active = False

        self.r_start = 0
        self.p_start = 0
        self.y_start = 0

    def isActive(self):
        return self.active

    def activateControl(self, roll, pitch, yaw):
        print("Activating with params RPY:{},{},{}".format(roll, pitch, yaw))
        self.active = True
        self.r_start = roll
        self.p_start = pitch
        self.y_start = yaw

    def deactivateControl(self):
        print("Deactivating")
        self.active = False

    def updateRollValue(self, val):
        print("Control got roll val {}".format(val))

    def updatePitchValue(self, val):
        print("Control got pitch val {}".format(val))

    def updateYawValue(self, val):
        print("Control got yaw val {}".format(val))


class C1(MIDIMapping):
    """ 
    uses the supplied midi port for cc and other midi messages
    Also connects to live directly through pylive for mixer signals (and possibly playback control)
    """

    def __init__(self, midiport):
        super().__init__(midiport)

        self.rr_val = 0
        self.rp_val = 0
        self.ry_val = 0
        self.lr_val = 0
        self.lp_val = 0
        self.ly_val = 0

        self.leftHandControls = []
        self.rightHandControls = []

        self.initLiveConnection()
        self.initControls()

        self.initUI()

    def initLiveConnection(self):
        self.liveset = live.Set()
        self.liveset.scan(scan_clip_names=True, scan_devices=True)
        for t in self.liveset.tracks:
            print("Track: {}".format(t.name))

    def initControls(self):
        for i in range(8):
            self.leftHandControls.append(C1Control())
            self.rightHandControls.append(C1Control())

    def initUI(self):
        self.widget = QLabel("Hi!")

    def rightRollChanged(self, val):
        for c in self.rightHandControls:
            if c.isActive():
                c.updateRollValue(val)

    def rightPitchChanged(self, val):
        for c in self.rightHandControls:
            if c.isActive():
                c.updatePitchValue(val)

    def rightYawChanged(self, val):
        for c in self.rightHandControls:
            if c.isActive():
                c.updateYawValue(val)

    def leftRollChanged(self, val):
        for c in self.leftHandControls:
            if c.isActive():
                c.updateRollValue(val)

    def leftPitchChanged(self, val):
        for c in self.leftHandControls:
            if c.isActive():
                c.updatePitchValue(val)

    def leftYawChanged(self, val):
        for c in self.leftHandControls:
            if c.isActive():
                c.updateYawValue(val)

    def fingerConnection(self, finger, con):
        if finger[0] == "R":
            carr = self.rightHandControls
            roll = self.rr_val
            pitch = self.rp_val
            yaw = self.ry_val
        else:
            carr = self.leftHandControls
            roll = self.lr_val
            pitch = self.lp_val
            yaw = self.ly_val

        idx = 0
        if finger[2] == "P":
            idx += 4

        if finger[1] == "M":
            idx += 1
        elif finger[1] == "R":
            idx += 2
        elif finger[1] == "P":
            idx += 3

        if con:
            carr[idx].activateControl(roll, pitch, yaw)
        else:
            carr[idx].deactivateControl()
