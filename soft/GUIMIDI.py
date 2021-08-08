import sys
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QSlider, QPushButton
from PyQt5.QtCore import Qt, QTimer
from rtmidi.midiutil import open_midioutput
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, CONTROL_CHANGE, PITCH_BEND
from pubsub import pub
import time
import numpy as np

from BoardInteraction import BoardInteractor


class ConfigWindow(QWidget):
    """
    """

    def __init__(self):
        QWidget.__init__(self)

        self.rr_ccnum = 22
        self.rp_ccnum = 23
        self.ry_ccnum = 24
        self.rr_enabled = True
        self.rp_enabled = True
        self.ry_enabled = True

        # value is the minimum delay in milliseconds between cc sends
        self.throttleLevels = [0, 33, 200, 1000]
        self.throttleLabels = ["None", "30Hz", "5Hz", "1Hz"]
        self.throttleLevel = 0

        self.midiout = None

        self.last_rgyro_time = 0
        self.last_lgyro_time = 0
        self.rrcint = False
        self.rpcint = False
        self.rycint = False

        self.board = None
        self.isStreaming = False

        self.rrcenter = 0.5
        self.rpcenter = 0.5
        self.rycenter = 0.5
        self.rrminval = 0.0
        self.rrmaxval = 1.0
        self.rpminval = 0.0
        self.rpmaxval = 1.0
        self.ryminval = 0.0
        self.rymaxval = 1.0
        self.calibActiveRoll = False
        self.calibActivePitch = False
        self.calibActiveYaw = False

        self.initUI()
        self.initBoardComs()
        self.initMIDI()

    def initUI(self):
        self.setWindowTitle("MIDI Glove Config")

        layout = QVBoxLayout()
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
        self.rrvalLabel = QLabel("0")
        l1.addWidget(QLabel("Value:"))
        l1.addWidget(self.rrvalLabel)
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
        self.rpvalLabel = QLabel("0")
        l2.addWidget(QLabel("Value:"))
        l2.addWidget(self.rpvalLabel)
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
        self.ryvalLabel = QLabel("0")
        l3.addWidget(QLabel("Value:"))
        l3.addWidget(self.ryvalLabel)
        layout.addLayout(l3)

        l4 = QHBoxLayout()
        self.throttleLabel = QLabel(self.throttleLabels[0])
        self.throttleSlider = QSlider(Qt.Horizontal)
        self.throttleSlider.setMinimum(0)
        self.throttleSlider.setMaximum(3)
        self.throttleSlider.setSingleStep(1)
        self.throttleSlider.valueChanged.connect(lambda: self.throttlestate(self.throttleSlider))
        l4.addWidget(self.throttleLabel)
        l4.addWidget(self.throttleSlider)
        layout.addLayout(l4)

        l5 = QHBoxLayout()
        self.streamButton = QPushButton("Stream")
        self.streamButton.clicked.connect(self.streambtn)
        l5.addWidget(self.streamButton)
        layout.addLayout(l5)

        l6 = QHBoxLayout()
        self.centerButton = QPushButton("Set Center")
        self.centerButton.clicked.connect(lambda: self.centerbtn(3))
        l6.addWidget(self.centerButton)
        self.centerYawButton = QPushButton("Center Yaw")
        self.centerYawButton.clicked.connect(lambda: self.centerYaw())
        l6.addWidget(self.centerYawButton)
        self.calibRollButton = QPushButton("Calibrate Roll")
        self.calibRollButton.clicked.connect(self.calibrollbtn)
        l6.addWidget(self.calibRollButton)
        self.calibPitchButton = QPushButton("Calibrate Pitch")
        self.calibPitchButton.clicked.connect(self.calibpitchbtn)
        l6.addWidget(self.calibPitchButton)
        self.calibYawButton = QPushButton("Calibrate Yaw")
        self.calibYawButton.clicked.connect(self.calibyawbtn)
        l6.addWidget(self.calibYawButton)
        self.calibLabel = QLabel("")
        l6.addWidget(self.calibLabel)
        layout.addLayout(l6)

        self.setLayout(layout)

    def streambtn(self):
        if self.isStreaming:
            self.isStreaming = False
            self.board.stop()
            self.board = None
            self.streamButton.setText("Stream")
        else:
            self.isStreaming = True
            self.board = BoardInteractor()
            self.board.start()
            self.streamButton.setText("Stop Streaming")

    def btnstate(self, ax, cb):
        if ax == "rr":
            self.rr_enabled = cb.isChecked()
        elif ax == "rp":
            self.rp_enabled = cb.isChecked()
        elif ax == "ry":
            self.ry_enabled = cb.isChecked()

    def spinstate(self, ax, sb):
        if ax == "rr":
            self.rr_ccnum = sb.value()
        elif ax == "rp":
            self.rp_ccnum = sb.value()
        elif ax == "ry":
            self.ry_ccnum = sb.value()

    def throttlestate(self, sld):
        self.throttleLabel.setText(self.throttleLabels[sld.value()])
        self.throttleLevel = self.throttleLevels[sld.value()]

    def centerbtn(self, timeleft):
        if timeleft > 0:
            self.calibLabel.setText(str(timeleft))
            QTimer.singleShot(1000, lambda: self.centerbtn(timeleft-1))
            return

        self.calibLabel.setText("")

        self.rrcenter = self.rrval_raw
        self.rpcenter = self.rpval_raw
        self.rycenter = self.ryval_raw

    def centerYaw(self):
        self.rycenter = self.ryval_raw

    def calibrollbtn(self):
        self.rrminval = self.rrval - 0.01
        self.rrmaxval = self.rrval - 0.01
        self.calibLabel.setText("Roll calibrating...")
        self.calibActiveRoll = True
        QTimer.singleShot(3000, self.calibrollfinish)

    def calibrollfinish(self):
        self.calibActiveRoll = False
        self.calibLabel.setText("")

    def calibpitchbtn(self):
        self.rpminval = self.rpval - 0.01
        self.rpmaxval = self.rpval - 0.01
        self.calibLabel.setText("Pitch calibrating...")
        self.calibActivePitch = True
        QTimer.singleShot(3000, self.calibpitchfinish)

    def calibpitchfinish(self):
        self.calibActivePitch = False
        self.calibLabel.setText("")

    def calibyawbtn(self):
        self.ryminval = self.ryval - 0.01
        self.rymaxval = self.ryval - 0.01
        self.calibLabel.setText("Yaw calibrating...")
        self.calibActiveYaw = True
        QTimer.singleShot(3000, self.calibyawfinish)

    def calibyawfinish(self):
        self.calibActiveYaw = False
        self.calibLabel.setText("")

    def initBoardComs(self):
        pub.subscribe(self.handleFingerConnection, 'FingerConnection')
        pub.subscribe(self.handleLGyroData, 'LGyro')
        pub.subscribe(self.handleRGyroData, 'RGyro')

    def initMIDI(self):
        self.midiout, self.midiportname = open_midioutput()

    def handleFingerConnection(self, con, finger):
        if self.midiout is None:
            return

    def handleLGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        if self.midiout is None:
            return

    def handleRGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        if self.midiout is None:
            return

        self.rrval_raw = roll
        self.rpval_raw = pitch
        self.ryval_raw = yaw
        self.rrval = roll - self.rrcenter + 0.5
        if self.rrval > 1.0:
            self.rrval -= 1.0
        self.rpval = pitch - self.rpcenter + 0.5
        if self.rpval > 1.0:
            self.rpval -= 1.0
        self.ryval = yaw - self.rycenter + 0.5
        if self.ryval > 1.0:
            self.ryval -= 1.0

        if self.calibActiveRoll:
            self.rrminval = min(self.rrminval, self.rrval)
            self.rrmaxval = max(self.rrmaxval, self.rrval)
        else:
            self.rrval = np.interp(self.rrval, [self.rrminval, 0.5, self.rrmaxval], [0.0, 0.5, 1.0])
        if self.calibActivePitch:
            self.rpminval = min(self.rpminval, self.rpval)
            self.rpmaxval = max(self.rpmaxval, self.rpval)
        else:
            self.rpval = np.interp(self.rpval, [self.rpminval, 0.5, self.rpmaxval], [0.0, 0.5, 1.0])
        if self.calibActiveYaw:
            self.ryminval = min(self.ryminval, self.ryval)
            self.rymaxval = max(self.rymaxval, self.ryval)
        else:
            self.ryval = np.interp(self.ryval, [self.ryminval, 0.5, self.rymaxval], [0.0, 0.5, 1.0])

        if time.time() * 1000 - self.last_rgyro_time < self.throttleLevel:
            self.rrcint = self.rrcint or rollChanged
            self.rpcint = self.rpcint or pitchChanged
            self.rycint = self.rycint or yawChanged
            # print("Throttling")
            return

        if rollChanged:
            self.rrvalLabel.setText(str(int(self.rrval*255)))
            if self.rr_enabled:
                self.cc(self.rr_ccnum, int(self.rrval*255))
        if pitchChanged:
            self.rpvalLabel.setText(str(int(self.rpval*255)))
            if self.rp_enabled:
                self.cc(self.rp_ccnum, int(self.rpval*255))
        if yawChanged:
            self.ryvalLabel.setText(str(int(self.ryval*255)))
            if self.ry_enabled:
                self.cc(self.ry_ccnum, int(self.ryval*255))

        self.last_rgyro_time = time.time() * 1000
        self.rrcint = False
        self.rpcint = False
        self.rycint = False

    def startNote(self, pitch=60, vel=112):
        self.midiout.send_message([NOTE_ON, pitch, vel])

    def stopNote(self, pitch=60):
        self.midiout.send_message([NOTE_OFF, pitch, 0])

    def cc(self, cc=0, value=0):
        if value < 0:
            # print("Correcting cc value {} to 0".format(value))
            value = 0
        if value > 255:
            # print("Correcting cc value {} to 255".format(value))
            value = 255
        self.midiout.send_message([CONTROL_CHANGE, cc, value])

    def pb(self, value=8192):
        self.midiout.send_message([PITCH_BEND, value & 0x7f, (value >> 7) & 0x7f])


def main():
    parent_app = QApplication(sys.argv)
    configWindow = ConfigWindow()
    configWindow.show()
    sys.exit(parent_app.exec_())


if __name__ == "__main__":
    main()
