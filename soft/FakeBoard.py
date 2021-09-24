from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QGridLayout, QButtonGroup, QRadioButton
from PyQt5.QtCore import Qt, QTimer
from pubsub import pub
import random


class FakeBoard(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.allfingers = ["LP", "LR", "LM", "LI", "RI", "RM", "RR", "RP"]
        self.fingerState = dict()
        for f in self.allfingers:
            self.fingerState[f + "T"] = False
            self.fingerState[f + "P"] = False

        self._lroll = 0.5
        self._lpitch = 0.5
        self._lyaw = 0.5
        self._rroll = 0.5
        self._rpitch = 0.5
        self._ryaw = 0.5

        self.initUI()

        if False:
            self.dataTimer = QTimer()
            self.dataTimer.timeout.connect(self.sendAData)
            self.dataTimer.start(1)

    def initUI(self):
        self.setWindowTitle("Gloves!")

        layout = QVBoxLayout()

        self.fingerDict = dict()

        def makeTogFunc(f, ff):
            return lambda: self.toggleFingerState(f + ff)

        g1 = QGridLayout()
        g1.addWidget(QLabel("Thumb"), 1, 0)
        g1.addWidget(QLabel("Palm"), 2, 0)
        for fi, f in enumerate(self.allfingers):
            g1.addWidget(QLabel(f), 0, fi+1)

            ttogbtn = QPushButton("Tog")
            ttogbtn.clicked.connect(makeTogFunc(f, "T"))
            tmombtn = QPushButton("Mom")
            tmombtn.pressed.connect(makeTogFunc(f, "T"))
            tmombtn.released.connect(makeTogFunc(f, "T"))
            tvb = QVBoxLayout()
            tvb.addWidget(ttogbtn)
            tvb.addWidget(tmombtn)
            self.fingerDict[f + "T"] = tmombtn
            tmombtn.setStyleSheet('QPushButton {background-color: white; border:  none}')
            g1.addLayout(tvb, 1, fi+1)

            ptogbtn = QPushButton("Tog")
            ptogbtn.clicked.connect(makeTogFunc(f, "P"))
            pmombtn = QPushButton("Mom")
            pmombtn.pressed.connect(makeTogFunc(f, "P"))
            pmombtn.released.connect(makeTogFunc(f, "P"))
            pvb = QVBoxLayout()
            pvb.addWidget(ptogbtn)
            pvb.addWidget(pmombtn)
            self.fingerDict[f + "P"] = pmombtn
            pmombtn.setStyleSheet('QPushButton {background-color: white; border:  none}')
            g1.addLayout(pvb, 2, fi+1)

        layout.addLayout(g1)

        def makeGyroFunc(s, ax):
            return lambda v: self.gyrovalChanged(s[0] + ax[0], float(v) / 100.0)

        g2 = QGridLayout()
        axes = ["Roll", "Pitch", "Yaw"]
        sides = ["Left", "Right"]
        for si, s in enumerate(sides):
            for ai, ax in enumerate(axes):
                fgw = FakeGyroWidget(ax)
                fgw.slider.valueChanged.connect(makeGyroFunc(s[0], ax[0]))
                g2.addWidget(fgw, ai, si)
                fgw.slider.valueChanged.emit(50)

        layout.addLayout(g2)

        self.setLayout(layout)

    def toggleFingerState(self, finger):
        self.setFingerState(finger, not self.fingerState[finger])

    def setFingerState(self, finger, state):
        self.fingerState[finger] = state
        # print(finger, state)
        pub.sendMessage('FingerConnection', con=state, finger=finger)
        if state:
            self.fingerDict[finger].setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.fingerDict[finger].setStyleSheet(
                'QPushButton {background-color: white; border:  none}')

    def gyrovalChanged(self, axis, val):
        if axis == "LR":
            self._lroll = val
        elif axis == "LP":
            self._lpitch = val
        elif axis == "LY":
            self._lyaw = val
        elif axis == "RR":
            self._rroll = val
        elif axis == "RP":
            self._rpitch = val
        elif axis == "RY":
            self._ryaw = val
        else:
            print("oifjewoijfewf??????", axis, val)

        if axis[0] == "L":
            pub.sendMessage('LGyro', roll=self._lroll, pitch=self._lpitch, yaw=self._lyaw,
                            rollChanged=axis == "LR", pitchChanged=axis == "LP", yawChanged=axis == "LY")
        else:
            pub.sendMessage('RGyro', roll=self._rroll, pitch=self._rpitch, yaw=self._ryaw,
                            rollChanged=axis == "RR", pitchChanged=axis == "RP", yawChanged=axis == "RY")
        # print(axis, val)

    def sendAData(self):
        print("Sending Random Data")
        self.gyrovalChanged("RR", random.random())
        self.gyrovalChanged("RP", random.random())
        self.gyrovalChanged("RY", random.random())


class FakeGyroWidget(QWidget):
    """
    Access self.slider and self.btnRand self.btnSin and self.btnStatic to set up your connections
    """

    def __init__(self, lbl):
        QWidget.__init__(self)

        g = QGridLayout()
        g.addWidget(QLabel(lbl), 0, 0)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setSingleStep(1)
        self.slider.setValue(50)
        g.addWidget(self.slider, 0, 1)
        vallbl = QLabel("0.5")
        self.slider.valueChanged.connect(lambda v: vallbl.setText(str(float(v) / 100.0)))
        g.addWidget(vallbl, 0, 2)

        # bg = QButtonGroup()
        # self.btnRand = QRadioButton("Random")
        # self.btnSin = QRadioButton("Sin")
        # self.btnStatic = QRadioButton("Static")
        # bg.addButton(self.btnRand)
        # bg.addButton(self.btnSin)
        # bg.addButton(self.btnStatic)

        # g.addWidget(self.btnRand, 1, 0)
        # g.addWidget(self.btnSin, 1, 1)
        # g.addWidget(self.btnStatic, 1, 2)

        self.setLayout(g)
