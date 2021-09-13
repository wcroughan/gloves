from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QComboBox, QSizePolicy, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPen
from PyQt5.QtCore import QRect, Qt, QSize
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, CONTROL_CHANGE, PITCH_BEND
import numpy as np
from scipy.interpolate import interp1d

from MIDI import MIDIMapping


class DragControl:
    def __init__(self, rollF=lambda v: None, rollFRange=(0.0, 1.0),
                 pitchF=lambda v: None, pitchFRange=(0.0, 1.0),
                 yawF=lambda v: None, yawFRange=(0.0, 1.0)):
        self.leftActive = False
        self.rightActive = False

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

        self.rEnabled = True
        self.pEnabled = True
        self.yEnabled = True

        self.widget = DragControlWidget(self)

    def isLeftActive(self):
        return self.leftActive

    def isRightActive(self):
        return self.rightActive

    def activateControl(self, roll, pitch, yaw, side):
        # expecting these to be in the 0.0-1.0 range
        # print("Activating with params RPY:{},{},{}, {}".format(roll, pitch, yaw, side))
        if side == "L":
            self.leftActive = True
        elif side == "R":
            self.rightActive = True
        else:
            raise Exception("asdf")
        # self.r_start = roll
        # self.p_start = pitch
        # self.y_start = yaw

    def deactivateControl(self, side):
        # print("Deactivating side {}".format(side))
        if side == "L":
            self.leftActive = False
        elif side == "R":
            self.rightActive = False
        else:
            raise Exception("asdf")
        # self.r_fval_start = self.r_fval
        # self.p_fval_start = self.p_fval
        # self.y_fval_start = self.y_fval

    # incoming diffs are on the 0-1 scale
    def updateRollValueDiff(self, diff):
        # print("Control got roll val diff {}".format(diff))
        self.r_fval = np.interp(self.r_fval + diff, [0.0, 1.0], [0.0, 1.0])
        self.r_fval_output = np.interp(self.r_fval, [0.0, 1.0], [self.rmin, self.rmax])
        if self.rEnabled:
            self.rfunc(self.r_fval_output)
        self.widget.setZ(self.r_fval)

    def updatePitchValueDiff(self, diff):
        # print("Control got pitch val diff {}".format(diff))
        self.p_fval = np.interp(self.p_fval + diff, [0.0, 1.0], [0.0, 1.0])
        self.p_fval_output = np.interp(self.p_fval, [0.0, 1.0], [self.pmin, self.pmax])
        if self.pEnabled:
            self.pfunc(self.p_fval_output)
        self.widget.setY(self.p_fval)

    def updateYawValueDiff(self, diff):
        # print("Control got yaw val diff {}".format(diff))
        self.y_fval = np.interp(self.y_fval + diff, [0.0, 1.0], [0.0, 1.0])
        self.y_fval_output = np.interp(self.y_fval, [0.0, 1.0], [self.ymin, self.ymax])
        if self.yEnabled:
            self.yfunc(self.y_fval_output)
        self.widget.setX(self.y_fval)

    def setREnabled(self, val):
        self.rEnabled = val

    def setPEnabled(self, val):
        self.pEnabled = val

    def setYEnabled(self, val):
        self.yEnabled = val


class DragControlXYPadWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.x = 0
        self.y = 0
        self.z = 0

        self.lineLen = 10
        self.pad = 3
        p = 3.14159265358979
        self.a1 = 5.0 / 8.0 * 2.0 * p
        self.a2 = -1.0 / 8.0 * 2.0 * p
        self.aFromZ = interp1d([0.0, 1.0], [self.a1, self.a2])

        self.guiSize = 100
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

    def paintEvent(self, event):
        # print("painting with {},{},{}".format(self.x, self.y, self.z))
        qp = QPainter(self)
        brush = QBrush()
        brush.setColor(QColor('black'))
        brush.setStyle(Qt.SolidPattern)
        rect = QRect(0, 0, qp.device().width(), qp.device().height())
        qp.fillRect(rect, brush)

        pen = QPen()
        pen.setWidth(3)
        pen.setColor(QColor('white'))
        qp.setPen(pen)
        x1 = self.pad + self.lineLen + (self.guiSize - 2 * self.pad - 2 * self.lineLen) * self.x
        y1 = self.pad + self.lineLen + (self.guiSize - 2 * self.pad - 2 * self.lineLen) * self.y
        # a = np.interp(self.z, [0.0, 1.0], [self.a1, self.a2])
        a = self.aFromZ(self.z)
        # print("{}->{}".format(self.z, a))
        x2 = x1 + self.lineLen * np.cos(a)
        y2 = y1 - self.lineLen * np.sin(a)
        qp.drawLine(x1, y1, x2, y2)

    def sizeHint(self):
        return QSize(self.guiSize, self.guiSize)

    def setX(self, val):
        self.x = val

    def setY(self, val):
        self.y = val

    def setZ(self, val):
        self.z = val


class DragControlWidget(QWidget):
    def __init__(self, control):
        super().__init__()

        self.rEnabled = True
        self.pEnabled = True
        self.yEnabled = True

        self._control = control

        self.initUI()

    def initUI(self):
        l1 = QHBoxLayout()
        self.rbut = QPushButton("R")
        self.rbut.clicked.connect(self.toggleREnabled)
        self.pbut = QPushButton("P")
        self.pbut.clicked.connect(self.togglePEnabled)
        self.ybut = QPushButton("Y")
        self.ybut.clicked.connect(self.toggleYEnabled)
        l1.addWidget(self.rbut)
        l1.addWidget(self.pbut)
        l1.addWidget(self.ybut)

        self.xyPad = DragControlXYPadWidget()

        l2 = QHBoxLayout()
        self.leftActiveButton = QPushButton("L")
        self.leftActiveButton.setEnabled(False)
        l2.addWidget(self.leftActiveButton)
        self.rightActiveButton = QPushButton("R")
        self.rightActiveButton.setEnabled(False)
        l2.addWidget(self.rightActiveButton)

        layout = QVBoxLayout()
        layout.addLayout(l1)
        layout.addWidget(self.xyPad)
        layout.addLayout(l2)

        self.setLayout(layout)

    def toggleREnabled(self):
        self.rEnabled = not self.rEnabled
        if self.rEnabled:
            self.rbut.setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.rbut.setStyleSheet(
                'QPushButton {background-color: white; border:  none}')

        self._control.setREnabled(self.rEnabled)
        self.update()

    def togglePEnabled(self):
        self.pEnabled = not self.pEnabled
        if self.pEnabled:
            self.pbut.setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.pbut.setStyleSheet(
                'QPushButton {background-color: white; border:  none}')

        self._control.setPEnabled(self.pEnabled)
        self.update()

    def toggleYEnabled(self):
        self.yEnabled = not self.yEnabled
        if self.yEnabled:
            self.ybut.setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.ybut.setStyleSheet(
                'QPushButton {background-color: white; border:  none}')

        self._control.setYEnabled(self.yEnabled)
        self.update()

    def setX(self, val):
        # print("Widget get val {}".format(val))
        self.xyPad.setX(val)
        self.update()

    def setY(self, val):
        # print("Widget get val {}".format(val))
        self.xyPad.setY(val)
        self.update()

    def setZ(self, val):
        # print("Widget get val {}".format(val))
        self.xyPad.setZ(val)
        self.update()

    def setLeftActive(self, val):
        if val:
            self.leftActiveButton.setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.leftActiveButton.setStyleSheet(
                'QPushButton {background-color: white; border:  none}')
        self.update()

    def setRightActive(self, val):
        if val:
            self.rightActiveButton.setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.rightActiveButton.setStyleSheet(
                'QPushButton {background-color: white; border:  none}')
        self.update()


class DragMap(MIDIMapping):
    """
    uses the supplied midi port for cc and other midi messages
    also connects to live directly through pylive for mixer signals (and possibly playback control)
    left hand does mod wheel, volume, and pan
    right hand does midi ccs
    """

    def __init__(self, midiport):
        super().__init__(midiport)
        self.ccstart = 32

        self.rr_val = 0
        self.rp_val = 0
        self.ry_val = 0
        self.lr_val = 0
        self.lp_val = 0
        self.ly_val = 0

        self.initControls()
        self.initWidget()
        self.widget.update()

    def initWidget(self):
        layout = QVBoxLayout()

        l1 = QHBoxLayout()
        l1.addWidget(self.controlDict["IT"].widget)
        l1.addWidget(self.controlDict["MT"].widget)
        l1.addWidget(self.controlDict["RT"].widget)
        l1.addWidget(self.controlDict["PT"].widget)
        layout.addLayout(l1)

        l2 = QHBoxLayout()
        l2.addWidget(self.controlDict["IP"].widget)
        l2.addWidget(self.controlDict["MP"].widget)
        l2.addWidget(self.controlDict["RP"].widget)
        l2.addWidget(self.controlDict["PP"].widget)
        layout.addLayout(l2)

        self.widget.setLayout(layout)

    def initControls(self):
        def makeCCFunc(chan, cc):
            def f(v):
                self.cc(cc=cc, value=v, channel=chan)
            return f

        self.controls = []
        self.controlDict = dict()

        cc = self.ccstart
        cons = ["IT", "MT", "RT", "PT", "IP", "MP", "RP", "PP"]
        for ci, c in enumerate(cons):
            dc = DragControl(rollF=makeCCFunc(1, cc), rollFRange=(0, 127),
                             pitchF=makeCCFunc(1, cc+1), pitchFRange=(0, 127),
                             yawF=makeCCFunc(1, cc+2), yawFRange=(0, 127))
            cc += 3
            self.controls.append(dc)
            self.controlDict[c] = dc

    def rightRollChanged(self, val):
        d = val - self.rr_val
        self.rr_val = val
        for ci, c in enumerate(self.controls):
            if c.isRightActive():
                c.updateRollValueDiff(d)

    def rightPitchChanged(self, val):
        d = val - self.rp_val
        self.rp_val = val
        for ci, c in enumerate(self.controls):
            if c.isRightActive():
                c.updatePitchValueDiff(d)

    def rightYawChanged(self, val):
        d = val - self.ry_val
        self.ry_val = val
        for ci, c in enumerate(self.controls):
            if c.isRightActive():
                c.updateYawValueDiff(d)

    def leftRollChanged(self, val):
        d = val - self.lr_val
        self.lr_val = val
        for ci, c in enumerate(self.controls):
            if c.isLeftActive():
                c.updateRollValueDiff(d)

    def leftPitchChanged(self, val):
        d = val - self.lp_val
        self.lp_val = val
        for ci, c in enumerate(self.controls):
            if c.isLeftActive():
                c.updatePitchValueDiff(d)

    def leftYawChanged(self, val):
        d = val - self.ly_val
        self.ly_val = val
        for ci, c in enumerate(self.controls):
            if c.isLeftActive():
                c.updateYawValueDiff(d)

    def fingerConnection(self, finger, con):
        if finger[0] == "R":
            roll = self.rr_val
            pitch = self.rp_val
            yaw = self.ry_val
        else:
            roll = self.lr_val
            pitch = self.lp_val
            yaw = self.ly_val

        print("(de)Activating {} ({}, {}, {}, {})".format(finger[1:], roll, pitch, yaw, finger[0]))
        if con:
            self.controlDict[finger[1:]].activateControl(roll, pitch, yaw, finger[0])
        else:
            self.controlDict[finger[1:]].deactivateControl(finger[0])
