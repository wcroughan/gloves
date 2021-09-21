import sys
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QSlider, QPushButton, QComboBox, QDialog
from PyQt5.QtCore import Qt, QTimer
from rtmidi.midiutil import open_midioutput
from pubsub import pub
import time
import numpy as np
from collections import deque

from FakeBoard import FakeBoard
from RealBoard import RealBoard
import ThreadExtension
from MIDI import M1, ToyMidiMap
from Drag import DragMap


class CalibrationDialog(QDialog):
    def __init__(self, side):
        super().__init__()

        self.setModal(False)
        self.side = side

        self.initUI()
        self.initBoardComs()

        self.TIME_BETWEEN_SAMPLE = 25  # ms
        self.TRIALS_PER_AXIS = 2
        self.ITERATIONS = 2
        self.TIME_PER_TRIAL = 1000

        self.SAMPLES_PER_AXIS = self.TIME_PER_TRIAL / self.TIME_BETWEEN_SAMPLE * \
            (self.TRIALS_PER_AXIS * self.ITERATIONS * 2 + 1)

        self.rollSamples = np.nan((3, self.SAMPLES_PER_AXIS))

        QTimer.singleShot(1000, self.startCalibration)

    def initUI(self):
        lbl1 = QLabel("Calibrating {} glove".format(self.side))
        self.actionLabel = QLabel("Move to center")
        layout = QVBoxLayout()
        layout.addWidget(lbl1)
        layout.addWidget(self.actionLabel)
        self.setLayout(layout)

    def initBoardComs(self):
        pub.subscribe(self.handleFingerConnection, 'FingerConnection')
        if self.side == "L":
            pub.subscribe(self.handleGyroData, 'LGyro')
        else:
            pub.subscribe(self.handleGyroData, 'RGyro')

    def startCalibration(self):
        pass

    def handleFingerConnection(self, con, finger):
        pass

    def handleGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        pass


class ConfigWindow(QWidget):
    """
    """

    def __init__(self):
        QWidget.__init__(self)

        # value is the minimum delay in milliseconds between cc sends
        self.throttleLevels = [0, 33, 200, 1000]
        self.throttleLabels = ["None", "30Hz", "5Hz", "1Hz"]
        self.throttleLevel = 0

        self.midiout = None
        self.midiHandler = None

        self.last_rgyro_time = 0
        self.last_lgyro_time = 0
        self.rrcint = False
        self.rpcint = False
        self.rycint = False
        self.lrcint = False
        self.lpcint = False
        self.lycint = False

        self.board = None

        self.rrcenter = 0.5
        self.rpcenter = 0.5
        self.rycenter = 0.5
        self.rrminval = 0.0
        self.rrmaxval = 1.0
        self.rpminval = 0.0
        self.rpmaxval = 1.0
        self.ryminval = 0.0
        self.rymaxval = 1.0
        self.lrcenter = 0.5
        self.lpcenter = 0.5
        self.lycenter = 0.5
        self.lrminval = 0.0
        self.lrmaxval = 1.0
        self.lpminval = 0.0
        self.lpmaxval = 1.0
        self.lyminval = 0.0
        self.lymaxval = 1.0
        self.calibActiveRollRight = False
        self.calibActivePitchRight = False
        self.calibActiveYawRight = False
        self.calibActiveRollLeft = False
        self.calibActivePitchLeft = False
        self.calibActiveYawLeft = False

        # None or (Roll|Pitch|Yaw|Center) (Right|Left)
        self.calibActive = "None"

        self.midiHandlerOptions = ["None",
                                   "M1",
                                   "ToyMidiMap",
                                   "Drag"
                                   ]

        self.inputOptions = ["None",
                             "Fake input",
                             "Arduino"]

        self.initUI()
        self.initBoardComs()
        self.initMIDI()

        self.midiHandlerComboBox.setCurrentIndex(3)
        self.inputComboBox.setCurrentIndex(1)

    def initUI(self):
        self.setWindowTitle("MIDI Glove Config")

        layout = QVBoxLayout()
        l5 = QHBoxLayout()
        l5.addWidget(QLabel("Output:"))
        self.midiHandlerComboBox = QComboBox()
        self.midiHandlerComboBox.addItems(self.midiHandlerOptions)
        self.midiHandlerComboBox.currentIndexChanged.connect(self.midiHandlerSelected)
        l5.addWidget(self.midiHandlerComboBox)
        layout.addLayout(l5)

        l7 = QHBoxLayout()
        l7.addWidget(QLabel("Input:"))
        self.inputComboBox = QComboBox()
        self.inputComboBox.addItems(self.inputOptions)
        self.inputComboBox.currentIndexChanged.connect(self.inputSelected)
        l7.addWidget(self.inputComboBox)
        layout.addLayout(l7)

        l6 = QHBoxLayout()
        self.leftCalibButton = QPushButton("Calib Left")
        self.leftCalibButton.clicked.connect(lambda: self.calibButton("L"))
        l6.addWidget(self.leftCalibButton)
        lCenterYawButton = QPushButton("Center Left Yaw")
        lCenterYawButton.clicked.connect(lambda: self.centerYaw("L"))
        lCenterYawButton.setEnabled(False)
        l6.addWidget(lCenterYawButton)
        self.rightCalibButton = QPushButton("Calib Right")
        self.rightCalibButton.clicked.connect(lambda: self.calibButton("R"))
        l6.addWidget(self.rightCalibButton)
        rCenterYawButton = QPushButton("Center Right Yaw")
        rCenterYawButton.clicked.connect(lambda: self.centerYaw("R"))
        rCenterYawButton.setEnabled(False)
        l6.addWidget(rCenterYawButton)
        layout.addLayout(l6)

        l4 = QHBoxLayout()
        self.throttleLabel = QLabel(self.throttleLabels[0])
        self.throttleSlider = QSlider(Qt.Horizontal)
        self.throttleSlider.setMinimum(0)
        self.throttleSlider.setMaximum(3)
        self.throttleSlider.setSingleStep(1)
        self.throttleSlider.valueChanged.connect(lambda: self.throttlestate(self.throttleSlider))
        l4.addWidget(QLabel("Throttle MIDI: "))
        l4.addWidget(self.throttleLabel)
        l4.addWidget(self.throttleSlider)
        layout.addLayout(l4)

        self.handlerWidgetContainer = QHBoxLayout()
        self.handlerWidget = QLabel("None")
        self.handlerWidgetContainer.addWidget(self.handlerWidget)
        layout.addLayout(self.handlerWidgetContainer)

        self.inputWidgetContainer = QHBoxLayout()
        self.inputWidget = QLabel("No input")
        self.inputWidgetContainer.addWidget(self.inputWidget)
        layout.addLayout(self.inputWidgetContainer)

        self.setLayout(layout)

    def midiHandlerSelected(self, idx):
        handler = self.midiHandlerOptions[idx]

        if handler == "M1":
            self.midiHandler = M1(self.midiout)
        elif handler == "ToyMidiMap":
            self.midiHandler = ToyMidiMap(self.midiout)
        elif handler == "Drag":
            self.midiHandler = DragMap(self.midiout)
        elif handler == "None":
            self.midiHandler = None
            self.handlerWidgetContainer.removeWidget(self.handlerWidget)
            self.handlerWidget.deleteLater()
            self.handlerWidget = QLabel("None")
            self.handlerWidgetContainer.addWidget(self.handlerWidget)
            return
        else:
            print("unimplemented handler")
            return

        self.handlerWidgetContainer.removeWidget(self.handlerWidget)
        self.handlerWidget.deleteLater()
        self.handlerWidget = self.midiHandler.widget
        self.handlerWidgetContainer.addWidget(self.handlerWidget)

    def inputSelected(self, idx):
        inp = self.inputOptions[idx]

        self.inputWidgetContainer.removeWidget(self.inputWidget)
        self.inputWidget.close()
        self.inputWidget.deleteLater()

        if inp == "None":
            self.inputWidget = QLabel("No Input")
        elif inp == "Arduino":
            self.inputWidget = RealBoard()
        elif inp == "Fake input":
            self.inputWidget = FakeBoard()
        else:
            print("Unimplemented input")
            return

        self.inputWidgetContainer.addWidget(self.inputWidget)

    def throttlestate(self, sld):
        self.throttleLabel.setText(self.throttleLabels[sld.value()])
        self.throttleLevel = self.throttleLevels[sld.value()]

    def centerbtn(self, timeleft, side):
        if timeleft > 0:
            if side == "L":
                self.calibLabel_l.setText(str(timeleft))
            else:
                self.calibLabel_r.setText(str(timeleft))
            QTimer.singleShot(1000, lambda: self.centerbtn(timeleft-1, side))
            return

        if side == "L":
            self.calibLabel_l.setText("")
            self.lrcenter = self.lrval_raw
            self.lpcenter = self.lpval_raw
            self.lycenter = self.lyval_raw
        else:
            self.calibLabel_r.setText("")
            self.rrcenter = self.rrval_raw
            self.rpcenter = self.rpval_raw
            self.rycenter = self.ryval_raw

    def centerYaw(self, side):
        if side == "L":
            self.lycenter = self.lyval_raw
        else:
            self.rycenter = self.ryval_raw

    def calibButton(self, side):
        # TODO go from center to roll calib to pitch to yaw and then back through again. Record all rpy coords
        # and then fit a line to each axis, and in the future project onto those three lines
        print("Initiating calibration on side {}".format(side))
        self.leftCalibButton.setEnabled(False)
        self.rightCalibButton.setEnabled(False)
        if side == "L":
            side = "Left"
            self.calibActiveCenterLeft = True
        else:
            side = "Right"
            self.calibActiveCenterRight = True
        self.calibDialog = QDialog()
        lbl1 = QLabel("Calibrating {} glove".format(side))
        self.calibDialogLabel = QLabel("Move to center")
        l = QVBoxLayout()
        l.addWidget(lbl1)
        l.addWidget(self.calibDialogLabel)
        self.calibDialog.setLayout(l)

        self.calibNextAxis = dict()
        self.calibNextAxis["Roll"] = "Pitch"
        self.calibNextAxis["Pitch"] = "Yaw"
        self.calibNextAxis["Yaw"] = "Roll"

        QTimer.singleShot(2000, lambda: self.calibPhase(1, "Roll"))

        self.calibDialog.setModal(False)
        self.calibDialog.exec_()

    def dialogUpdateSeries(self, series, delay):
        if len(series) == 0:
            return

        s = series.pop()
        self.calibDialogLabel.setText(s)
        QTimer.singleShot(delay, lambda: self.dialogUpdateSeries(series, delay))

    def calibPhase(self, nRepeats, axis):
        if self.calibActiveCenterLeft:
            self.calibActiveRollLeft = True
            self.calibActiveCenterLeft = False
        else:
            self.calibActiveRollRight = True
            self.calibActiveCenterRight = False
        print("Initiating calib roll phase with {} repeats".format(nRepeats))
        if nRepeats <= 0:
            self.calibActiveRollLeft = False
            self.calibActiveRollRight = False
            self.leftCalibButton.setEnabled(True)
            self.rightCalibButton.setEnabled(True)
            self.calibDialog.done(0)
        else:
            cmds = deque([])
            cmds.appendleft("Roll left")
            cmds.appendleft("Roll right")
            cmds.appendleft("Roll left")
            cmds.appendleft("Roll right")
            cmds.appendleft("Roll center")
            self.dialogUpdateSeries(cmds, 1000)
            QTimer.singleShot(1000 * (len(cmds)+1), lambda: self.calibPhase(nRepeats - 1))

    def calibrollbtn(self, side):
        if side == "L":
            self.lrminval = self.lrval - 0.01
            self.lrmaxval = self.lrval - 0.01
            self.calibLabel_l.setText("Roll calibrating...")
            self.calibActiveRollLeft = True
        else:
            self.rrminval = self.rrval - 0.01
            self.rrmaxval = self.rrval - 0.01
            self.calibLabel_r.setText("Roll calibrating...")
            self.calibActiveRollRight = True

        QTimer.singleShot(3000, lambda: self.calibrollfinish(side))

    def calibrollfinish(self, side):
        if side == "L":
            self.calibActiveRollLeft = False
            self.calibLabel_l.setText("")
        else:
            self.calibActiveRollRight = False
            self.calibLabel_r.setText("")

    def calibpitchbtn(self, side):
        if side == "L":
            self.lpminval = self.lpval - 0.01
            self.lpmaxval = self.lpval - 0.01
            self.calibLabel_l.setText("Pitch calibrating...")
            self.calibActivePitchLeft = True
        else:
            self.rpminval = self.rpval - 0.01
            self.rpmaxval = self.rpval - 0.01
            self.calibLabel_r.setText("Pitch calibrating...")
            self.calibActivePitchRight = True

        QTimer.singleShot(3000, lambda: self.calibpitchfinish(side))

    def calibpitchfinish(self, side):
        if side == "L":
            self.calibActivePitchLeft = False
            self.calibLabel_l.setText("")
        else:
            self.calibActivePitchRight = False
            self.calibLabel_r.setText("")

    def calibyawbtn(self, side):
        if side == "L":
            self.lyminval = self.lyval - 0.01
            self.lymaxval = self.lyval - 0.01
            self.calibLabel_l.setText("Yaw calibrating...")
            self.calibActiveYawLeft = True
        else:
            self.ryminval = self.ryval - 0.01
            self.rymaxval = self.ryval - 0.01
            self.calibLabel_r.setText("Yaw calibrating...")
            self.calibActiveYawRight = True
        QTimer.singleShot(3000, lambda: self.calibyawfinish(side))

    def calibyawfinish(self, side):
        if side == "L":
            self.calibActiveYawLeft = False
            self.calibLabel_l.setText("")
        else:
            self.calibActiveYawRight = False
            self.calibLabel_r.setText("")

    def initBoardComs(self):
        pub.subscribe(self.handleFingerConnection, 'FingerConnection')
        pub.subscribe(self.handleLGyroData, 'LGyro')
        pub.subscribe(self.handleRGyroData, 'RGyro')

    def initMIDI(self):
        self.midiout, self.midiportname = open_midioutput()

    def handleFingerConnection(self, con, finger):
        if self.midiHandler is not None:
            self.midiHandler.fingerConnection(finger, con)

    def handleLGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        self.lrval_raw = roll
        self.lpval_raw = pitch
        self.lyval_raw = yaw
        self.lrval = roll - self.lrcenter + 0.5
        if self.lrval > 1.0:
            self.lrval -= 1.0
        self.lpval = pitch - self.lpcenter + 0.5
        if self.lpval > 1.0:
            self.lpval -= 1.0
        self.lyval = yaw - self.lycenter + 0.5
        if self.lyval > 1.0:
            self.lyval -= 1.0

        if self.calibActiveRollLeft:
            self.lrminval = min(self.lrminval, self.lrval)
            self.lrmaxval = max(self.lrmaxval, self.lrval)
            print(self.lrval)
        else:
            self.lrval = np.interp(self.lrval, [self.lrminval, 0.5, self.lrmaxval], [0.0, 0.5, 1.0])
        if self.calibActivePitchLeft:
            self.lpminval = min(self.lpminval, self.lpval)
            self.lpmaxval = max(self.lpmaxval, self.lpval)
        else:
            self.lpval = np.interp(self.lpval, [self.lpminval, 0.5, self.lpmaxval], [0.0, 0.5, 1.0])
        if self.calibActiveYawLeft:
            self.lyminval = min(self.lyminval, self.lyval)
            self.lymaxval = max(self.lymaxval, self.lyval)
        else:
            self.lyval = np.interp(self.lyval, [self.lyminval, 0.5, self.lymaxval], [0.0, 0.5, 1.0])

        if time.time() * 1000 - self.last_lgyro_time < self.throttleLevel:
            self.lrcint = self.lrcint or rollChanged
            self.lpcint = self.lpcint or pitchChanged
            self.lycint = self.lycint or yawChanged
            # print("Throttling")
            return

        if rollChanged:
            if self.midiHandler is not None:
                self.midiHandler.leftRollChanged(self.lrval)
        if pitchChanged:
            if self.midiHandler is not None:
                self.midiHandler.leftPitchChanged(self.lpval)
        if yawChanged:
            if self.midiHandler is not None:
                self.midiHandler.leftYawChanged(self.lyval)

        self.last_lgyro_time = time.time() * 1000
        self.lrcint = False
        self.lpcint = False
        self.lycint = False

    def handleRGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        # print("RGYRO received:", roll, pitch, yaw)
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

        if self.calibActiveRollRight:
            self.rrminval = min(self.rrminval, self.rrval)
            self.rrmaxval = max(self.rrmaxval, self.rrval)
        else:
            self.rrval = np.interp(self.rrval, [self.rrminval, 0.5, self.rrmaxval], [0.0, 0.5, 1.0])
        if self.calibActivePitchRight:
            self.rpminval = min(self.rpminval, self.rpval)
            self.rpmaxval = max(self.rpmaxval, self.rpval)
        else:
            self.rpval = np.interp(self.rpval, [self.rpminval, 0.5, self.rpmaxval], [0.0, 0.5, 1.0])
        if self.calibActiveYawRight:
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
            if self.midiHandler is not None:
                self.midiHandler.rightRollChanged(self.rrval)
        if pitchChanged:
            if self.midiHandler is not None:
                self.midiHandler.rightPitchChanged(self.rpval)
        if yawChanged:
            if self.midiHandler is not None:
                self.midiHandler.rightYawChanged(self.ryval)

        self.last_rgyro_time = time.time() * 1000
        self.rrcint = False
        self.rpcint = False
        self.rycint = False


def main():
    parent_app = QApplication(sys.argv)
    configWindow = ConfigWindow()
    configWindow.show()
    sys.exit(parent_app.exec_())


if __name__ == "__main__":
    main()
