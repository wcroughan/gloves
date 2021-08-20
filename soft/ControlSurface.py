import numpy as np
from PyQt5.QtWidgets import QLabel
from MIDI import MIDIMapping
import live


class C1Control:
    def __init__(self, rollF=lambda v: None, rollFRange=(0.0, 1.0),
                 pitchF=lambda v: None, pitchFRange=(0.0, 1.0),
                 yawF=lambda v: None, yawFRange=(0.0, 1.0)):
        self.active = False

        self.r_start = 0
        self.p_start = 0
        self.y_start = 0

        self.r_fval_start = 0
        self.r_fval = 0
        self.p_fval_start = 0
        self.p_fval = 0
        self.y_fval_start = 0
        self.y_fval = 0

        self.rfunc = rollF
        self.pfunc = pitchF
        self.yfunc = yawF

        self.rmin = rollFRange[0]
        self.rmax = rollFRange[1]
        self.pmin = pitchFRange[0]
        self.pmax = pitchFRange[1]
        self.ymin = yawFRange[0]
        self.ymax = yawFRange[1]

    def isActive(self):
        return self.active

    def activateControl(self, roll, pitch, yaw):
        # expecting these to be in the 0.0-1.0 range
        print("Activating with params RPY:{},{},{}".format(roll, pitch, yaw))
        self.active = True
        self.r_start = roll
        self.p_start = pitch
        self.y_start = yaw

    def deactivateControl(self):
        print("Deactivating")
        self.active = False
        self.r_fval_start = self.r_fval
        self.p_fval_start = self.p_fval
        self.y_fval_start = self.y_fval

    # val should be in [0.0-1.0]
    def updateRollValue(self, val):
        if not self.active:
            return

        print("Control got roll val {}".format(val))
        self.r_fval = val - self.r_start + self.r_fval_start
        self.rfunc(np.interp1(self.r_fval, [0.0, 1.0], [self.rmin, self.rmax]))

    def updatePitchValue(self, val):
        if not self.active:
            return

        print("Control got pitch val {}".format(val))
        self.p_fval = val - self.p_start + self.p_fval_start
        self.pfunc(np.interp1(self.p_fval, [0.0, 1.0], [self.pmin, self.pmax]))

    def updateYawValue(self, val):
        if not self.active:
            return

        print("Control got yaw val {}".format(val))
        self.y_fval = val - self.y_start + self.y_fval_start
        self.yfunc(np.interp1(self.y_fval, [0.0, 1.0], [self.ymin, self.ymax]))


class C1(MIDIMapping):
    """
    uses the supplied midi port for cc and other midi messages
    also connects to live directly through pylive for mixer signals (and possibly playback control)
    left hand does mod wheel, volume, and pan
    right hand does midi ccs
    """

    def __init__(self, midiport):
        super().__init__(midiport)

        self.l_roll_ccnum = 1
        self.r_roll_ccnum = 22
        self.r_pitch_ccnum = 23
        self.r_yaw_ccnum = 24

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
        def makeVolumeControlFunc(i):
            def f(v):
                self.liveset.tracks[i].volume = v
            return f

        def makePanControlFunc(i):
            def f(v):
                self.liveset.tracks[i].pan = v
            return f

        def makeCCFunc(chan, cc):
            def f(v):
                self.cc(cc=cc, value=v, channel=chan)
            return f

        for i in range(8):
            lc = C1Control(rollF=makeCCFunc(i, self.l_roll_ccnum), rollFRange=(0, 127),
                           pitchF=makeVolumeControlFunc(i), pitchFRange=(0.0, 1.0),
                           yawF=makePanControlFunc(i), yawFRange=(0.0, 1.0))
            rc = C1Control(rollF=makeCCFunc(i, self.r_roll_ccnum), rollFRange=(0, 127),
                           pitchF=makeCCFunc(i, self.r_pitch_ccnum), pitchFRange=(0, 127),
                           yawF=makeCCFunc(i, self.r_yaw_ccnum), yawFRange=(0, 127))
            self.leftHandControls.append(lc)
            self.rightHandControls.append(rc)

    def initUI(self):
        self.widget = QLabel("Hi!")

    def rightRollChanged(self, val):
        self.rr_val = val
        for c in self.rightHandControls:
            if c.isActive():
                c.updateRollValue(val)

    def rightPitchChanged(self, val):
        self.rp_val = val
        for c in self.rightHandControls:
            if c.isActive():
                c.updatePitchValue(val)

    def rightYawChanged(self, val):
        self.ry_val = val
        for c in self.rightHandControls:
            if c.isActive():
                c.updateYawValue(val)

    def leftRollChanged(self, val):
        self.lr_val = val
        for c in self.leftHandControls:
            if c.isActive():
                c.updateRollValue(val)

    def leftPitchChanged(self, val):
        self.lp_val = val
        for c in self.leftHandControls:
            if c.isActive():
                c.updatePitchValue(val)

    def leftYawChanged(self, val):
        self.ly_val = val
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
