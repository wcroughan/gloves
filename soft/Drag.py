from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QComboBox
from PyQt5.QtGui import QPixmap, QPainter
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, CONTROL_CHANGE, PITCH_BEND
import numpy as np

from MIDI import MIDIMapping


class DragControl:
    def __init__(self, rollF=lambda v: None, rollFRange=(0.0, 1.0),
                 pitchF=lambda v: None, pitchFRange=(0.0, 1.0),
                 yawF=lambda v: None, yawFRange=(0.0, 1.0)):
        self.active = False

        self.r_start = 0
        self.p_start = 0
        self.y_start = 0

        self.r_fval_start = 0
        self.r_fval = 0
        self.r_fval_output = 0
        self.p_fval_start = 0
        self.p_fval = 0
        self.p_fval_output = 0
        self.y_fval_start = 0
        self.y_fval = 0
        self.y_fval_output = 0

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
        self.r_fval = np.interp(val - self.r_start + self.r_fval_start, [0.0, 1.0], [0.0, 1.0])
        self.r_fval_output = np.interp(self.r_fval, [0.0, 1.0], [self.rmin, self.rmax])
        self.rfunc(self.r_fval_output)

    def updatePitchValue(self, val):
        if not self.active:
            return

        print("Control got pitch val {}".format(val))
        self.p_fval = np.interp(val - self.p_start + self.p_fval_start, [0.0, 1.0], [0.0, 1.0])
        self.p_fval_output = np.interp(self.p_fval, [0.0, 1.0], [self.pmin, self.pmax])
        self.pfunc(self.p_fval_output)

    def updateYawValue(self, val):
        if not self.active:
            return

        print("Control got yaw val {}".format(val))
        self.y_fval = np.interp(val - self.y_start + self.y_fval_start, [0.0, 1.0], [0.0, 1.0])
        self.y_fval_output = np.interp(self.y_fval, [0.0, 1.0], [self.ymin, self.ymax])
        self.yfunc(self.y_fval_output)


class DragControlWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel()
        canvas = QPixmap(300, 300)
        self.label.setPixmap(canvas)
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.drawSomething()

    def drawSomething(self):
        pt = QPainter(self.label.pixmap())
        pt.drawLine(10, 10, 300, 200)
        pt.end()


class DragMap(MIDIMapping):
    """
    uses the supplied midi port for cc and other midi messages
    also connects to live directly through pylive for mixer signals (and possibly playback control)
    left hand does mod wheel, volume, and pan
    right hand does midi ccs
    """

    def __init__(self, midiport):
        super().__init__(midiport)

        self.lr_ccnum = 1  # mod wheel
        self.lp_ccnum = 102  # mapped to volume
        self.ly_ccnum = 103  # mapped to pan
        self.rr_ccnum = 22
        self.rp_ccnum = 23
        self.ry_ccnum = 24

        self.rr_enabled = True
        self.rp_enabled = True
        self.ry_enabled = True
        self.lr_enabled = True
        self.lp_enabled = True
        self.ly_enabled = True

        self.rr_val = 0
        self.rp_val = 0
        self.ry_val = 0
        self.lr_val = 0
        self.lp_val = 0
        self.ly_val = 0

        self.leftHandControls = []
        self.rightHandControls = []

        self.initWidget()
        self.initControls()
        self.widget.update()

    def initWidget(self):
        layout = QVBoxLayout()

        cw = DragControlWidget()
        layout.addWidget(cw)

        l1 = QHBoxLayout()
        l1.addWidget(QLabel("Right Roll"))
        self.rrcb = QCheckBox("Enabled")
        self.rrcb.setChecked(self.rr_enabled)
        self.rrcb.stateChanged.connect(lambda: self.btnstate("rr", self.rrcb))
        l1.addWidget(QLabel("Midi cc:"))
        self.rrsb = QSpinBox()
        self.rrsb.setValue(self.rr_ccnum)
        self.rrsb.valueChanged.connect(lambda: self.spinstate("rr", self.rrsb))
        l1.addWidget(self.rrsb)
        l1.addWidget(self.rrcb)
        self.rrvalLabels = []
        l1.addWidget(QLabel("Values:"))
        for i in range(8):
            self.rrvalLabels.append(QLabel("-"))
            l1.addWidget(self.rrvalLabels[i])
        layout.addLayout(l1)

        l2 = QHBoxLayout()
        l2.addWidget(QLabel("Right Pitch"))
        self.rpcb = QCheckBox("Enabled")
        self.rpcb.setChecked(self.rp_enabled)
        self.rpcb.stateChanged.connect(lambda: self.btnstate("rp", self.rpcb))
        l2.addWidget(QLabel("Midi cc:"))
        self.rpsb = QSpinBox()
        self.rpsb.setValue(self.rp_ccnum)
        self.rpsb.valueChanged.connect(lambda: self.spinstate("rp", self.rpsb))
        l2.addWidget(self.rpsb)
        l2.addWidget(self.rpcb)
        self.rpvalLabels = []
        l2.addWidget(QLabel("Values:"))
        for i in range(8):
            self.rpvalLabels.append(QLabel("-"))
            l2.addWidget(self.rpvalLabels[i])
        layout.addLayout(l2)

        l3 = QHBoxLayout()
        l3.addWidget(QLabel("Right Yaw"))
        self.rycb = QCheckBox("Enabled")
        self.rycb.setChecked(self.ry_enabled)
        self.rycb.stateChanged.connect(lambda: self.btnstate("ry", self.rycb))
        l3.addWidget(QLabel("Midi cc:"))
        self.rysb = QSpinBox()
        self.rysb.setValue(self.ry_ccnum)
        self.rysb.valueChanged.connect(lambda: self.spinstate("ry", self.rysb))
        l3.addWidget(self.rysb)
        l3.addWidget(self.rycb)
        self.ryvalLabels = []
        l3.addWidget(QLabel("Values:"))
        for i in range(8):
            self.ryvalLabels.append(QLabel("-"))
            l3.addWidget(self.ryvalLabels[i])
        layout.addLayout(l3)

        l4 = QHBoxLayout()
        l4.addWidget(QLabel("Left Roll"))
        self.lrcb = QCheckBox("Enabled")
        self.lrcb.setChecked(self.lr_enabled)
        self.lrcb.stateChanged.connect(lambda: self.btnstate("lr", self.lrcb))
        l4.addWidget(QLabel("Midi cc:"))
        self.lrsb = QSpinBox()
        self.lrsb.setValue(self.lr_ccnum)
        self.lrsb.valueChanged.connect(lambda: self.spinstate("lr", self.lrsb))
        l4.addWidget(self.lrsb)
        l4.addWidget(self.lrcb)
        self.lrvalLabels = []
        l4.addWidget(QLabel("Values:"))
        for i in range(8):
            self.lrvalLabels.append(QLabel("-"))
            l4.addWidget(self.lrvalLabels[i])
        layout.addLayout(l4)

        l5 = QHBoxLayout()
        l5.addWidget(QLabel("Left Pitch"))
        self.lpcb = QCheckBox("Enabled")
        self.lpcb.setChecked(self.lp_enabled)
        self.lpcb.stateChanged.connect(lambda: self.btnstate("lp", self.lpcb))
        l5.addWidget(QLabel("Midi cc:"))
        self.lpsb = QSpinBox()
        self.lpsb.setValue(self.lp_ccnum)
        self.lpsb.valueChanged.connect(lambda: self.spinstate("lp", self.lpsb))
        l5.addWidget(self.lpsb)
        l5.addWidget(self.lpcb)
        self.lpvalLabels = []
        l5.addWidget(QLabel("Values:"))
        for i in range(8):
            self.lpvalLabels.append(QLabel("-"))
            l5.addWidget(self.lpvalLabels[i])
        layout.addLayout(l5)

        l6 = QHBoxLayout()
        l6.addWidget(QLabel("Left Yaw"))
        self.lycb = QCheckBox("Enabled")
        self.lycb.setChecked(self.ly_enabled)
        self.lycb.stateChanged.connect(lambda: self.btnstate("ly", self.lycb))
        l6.addWidget(QLabel("Midi cc:"))
        self.lysb = QSpinBox()
        self.lysb.setValue(self.ly_ccnum)
        self.lysb.valueChanged.connect(lambda: self.spinstate("ly", self.lysb))
        l6.addWidget(self.lysb)
        l6.addWidget(self.lycb)
        self.lyvalLabels = []
        l6.addWidget(QLabel("Values:"))
        for i in range(8):
            self.lyvalLabels.append(QLabel("-"))
            l6.addWidget(self.lyvalLabels[i])
        layout.addLayout(l6)

        self.widget.setLayout(layout)

    def btnstate(self, ax, cb):
        if ax == "rr":
            self.rr_enabled = cb.isChecked()
        elif ax == "rp":
            self.rp_enabled = cb.isChecked()
        elif ax == "ry":
            self.ry_enabled = cb.isChecked()
        elif ax == "lr":
            self.lr_enabled = cb.isChecked()
        elif ax == "lp":
            self.lp_enabled = cb.isChecked()
        elif ax == "ly":
            self.ly_enabled = cb.isChecked()

    def spinstate(self, ax, sb):
        if ax == "rr":
            self.rr_ccnum = sb.value()
        elif ax == "rp":
            self.rp_ccnum = sb.value()
        elif ax == "ry":
            self.ry_ccnum = sb.value()
        elif ax == "lr":
            self.lr_ccnum = sb.value()
        elif ax == "lp":
            self.lp_ccnum = sb.value()
        elif ax == "ly":
            self.ly_ccnum = sb.value()

    def initControls(self):
        def makeCCFunc(chan, cc):
            def f(v):
                self.cc(cc=cc, value=v, channel=chan)
            return f

        for i in range(8):
            lc = DragControl(rollF=makeCCFunc(i, self.lr_ccnum), rollFRange=(0, 127),
                             pitchF=makeCCFunc(i, self.lp_ccnum), pitchFRange=(0, 127),
                             yawF=makeCCFunc(i, self.ly_ccnum), yawFRange=(0, 127))
            rc = DragControl(rollF=makeCCFunc(i, self.rr_ccnum), rollFRange=(0, 127),
                             pitchF=makeCCFunc(i, self.rp_ccnum), pitchFRange=(0, 127),
                             yawF=makeCCFunc(i, self.ry_ccnum), yawFRange=(0, 127))
            self.leftHandControls.append(lc)
            self.rightHandControls.append(rc)

    def rightRollChanged(self, val):
        self.rr_val = val
        for ci, c in enumerate(self.rightHandControls):
            if c.isActive():
                c.updateRollValue(val)
                self.rrvalLabels[ci].setText("{:.2f}".format(c.r_fval_output))

    def rightPitchChanged(self, val):
        self.rp_val = val
        for ci, c in enumerate(self.rightHandControls):
            if c.isActive():
                c.updatePitchValue(val)
                self.rpvalLabels[ci].setText("{:.2f}".format(c.p_fval_output))

    def rightYawChanged(self, val):
        self.ry_val = val
        for ci, c in enumerate(self.rightHandControls):
            if c.isActive():
                c.updateYawValue(val)
                self.ryvalLabels[ci].setText("{:.2f}".format(c.y_fval_output))

    def leftRollChanged(self, val):
        self.lr_val = val
        for ci, c in enumerate(self.leftHandControls):
            if c.isActive():
                c.updateRollValue(val)
                self.lrvalLabels[ci].setText("{:.2f}".format(c.r_fval_output))

    def leftPitchChanged(self, val):
        self.lp_val = val
        for ci, c in enumerate(self.leftHandControls):
            if c.isActive():
                c.updatePitchValue(val)
                self.lpvalLabels[ci].setText("{:.2f}".format(c.p_fval_output))

    def leftYawChanged(self, val):
        self.ly_val = val
        for ci, c in enumerate(self.leftHandControls):
            if c.isActive():
                c.updateYawValue(val)
                self.lyvalLabels[ci].setText("{:.2f}".format(c.y_fval_output))

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
