import sys
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QSlider, QPushButton, QComboBox, QDialog
from PyQt5.QtCore import Qt, QTimer
from rtmidi.midiutil import open_midioutput
from pubsub import pub
import time
import numpy as np
from collections import deque
from sklearn.decomposition import FastICA
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d


from FakeBoard import FakeBoard
from RealBoard import RealBoard
import ThreadExtension
from MIDI import M1, ToyMidiMap
from Drag import DragMap


class CalibrationDialog(QDialog):
    def __init__(self, side):
        super().__init__()

        # self.setModal(False)
        self.side = side

        self.initUI()
        self.initBoardComs()

        self.TIME_BETWEEN_SAMPLE = 25  # ms
        self.TRIALS_PER_AXIS = 2

        self.DEBUG_MODE = True
        if not self.DEBUG_MODE:
            self.ITERATIONS = 2
            self.SAMPLES_PER_TRIAL = 40
        else:
            self.ITERATIONS = 1
            self.SAMPLES_PER_TRIAL = 10
        self.TIME_PER_TRIAL = self.TIME_BETWEEN_SAMPLE * self.SAMPLES_PER_TRIAL

        self.SAMPLES_PER_AXIS = self.TIME_PER_TRIAL * \
            (self.TRIALS_PER_AXIS * 2 + 1) * self.ITERATIONS

        self.NUM_CENTER_SAMPLES = self.ITERATIONS * 3

        self.sampleBuffer = np.empty((3, self.SAMPLES_PER_AXIS * 3))
        self.centerBuffer = np.empty((3, self.NUM_CENTER_SAMPLES))
        self.axisEndBuffer = np.empty((3, 3))
        self.sampleBuffer[:] = np.nan
        self.centerBuffer[:] = np.nan
        self.captureNextCenter = False
        self.captureNextAxis = None
        self.centeri = 0
        self.samplei = 0
        self.nextSampleT = 0

        if self.DEBUG_MODE:
            self.centerBuffer[:] = 0.5
            self.sampleBuffer[:] = 0.5
            self.sampleBuffer[0, 0:4] = np.linspace(0.3, 0.7, 4)
            self.sampleBuffer[1, 4:8] = np.linspace(0.1, 0.9, 4)
            self.sampleBuffer[2, 8:12] = np.linspace(0, 1, 4)
            self.centeri = self.NUM_CENTER_SAMPLES
            self.samplei = self.SAMPLES_PER_AXIS * 3
            self.axisEndBuffer[:] = 0.5
            self.axisEndBuffer = self.axisEndBuffer - 0.5 * np.eye(3)
            print(self.axisEndBuffer)

        QTimer.singleShot(1000, self.startCalibration)

    def initUI(self):
        lbl1 = QLabel("Calibrating {} glove".format(self.side))
        self.actionLabel = QLabel("Move to center")
        layout = QVBoxLayout()
        layout.addWidget(lbl1)
        layout.addWidget(self.actionLabel)
        self.setLayout(layout)

    def initBoardComs(self):
        if self.side == "L":
            pub.subscribe(self.handleGyroData, 'LGyro')
        else:
            pub.subscribe(self.handleGyroData, 'RGyro')

    def startCalibration(self):
        # QTimer.singleShot(0, lambda: self.calibrationPhase(0, 0, 0))
        self.captureNextCenter = True
        self.calibrationPhase(0, 0, 0)

    def calibrationPhase(self, iteration, axis, trial):
        if trial == self.TRIALS_PER_AXIS * 2 + 1:
            axis = (axis + 1) % 3
            if axis == 0:
                iteration += 1
                if iteration == self.ITERATIONS:
                    self.finishCalibration()
                    return

            self.captureNextCenter = True
            self.calibrationPhase(iteration, axis, 0)
            return

        lblstr = ""
        if trial == self.TRIALS_PER_AXIS * 2:
            lblstr = "Return to center"
            self.captureNextAxis = axis
        else:
            if axis == 0:
                lblstr = "Roll "
            elif axis == 1:
                lblstr = "Pitch "
            elif axis == 2:
                lblstr = "Yaw "

            if trial % 2 == 0:
                lblstr += "Up"
            else:
                lblstr += "Down"

        self.actionLabel.setText(lblstr)

        QTimer.singleShot(self.TIME_PER_TRIAL,
                          lambda: self.calibrationPhase(iteration, axis, trial+1))

    def finishCalibration(self):
        if self.side == "L":
            pub.unsubscribe(self.handleGyroData, 'LGyro')
        else:
            pub.unsubscribe(self.handleGyroData, 'RGyro')

        print(self.sampleBuffer)
        print(self.centerBuffer)
        self.sampleBuffer = self.sampleBuffer[:, 0:self.samplei]
        self.centerBuffer = self.centerBuffer[:, 0:self.centeri]
        self.actionLabel.setText("Calibrating, please wait...")

        self.center = np.mean(self.centerBuffer, axis=1)
        print(self.center)
        print(self.sampleBuffer)
        self.sampleBuffer = self.sampleBuffer.T - self.center

        self.ica = FastICA()
        newcoords = self.ica.fit_transform(self.sampleBuffer)
        print(newcoords)

        self.axisEndBuffer = self.axisEndBuffer.T - self.center
        endcoords = self.ica.transform(self.axisEndBuffer)
        print(endcoords)
        self.axes = np.argmax(np.abs(endcoords), axis=1)
        print(self.axes)

        axismins = np.min(newcoords, axis=0)
        axismaxs = np.max(newcoords, axis=0)
        self.axisranges = np.zeros((3, 3))
        self.axisranges[:, 0] = axismins
        self.axisranges[:, 2] = axismaxs
        for i in range(3):
            if endcoords[i, self.axes[i]] > 0:
                tmp = self.axisranges[i, 0]
                self.axisranges[i, 0] = self.axisranges[i, 2]
                self.axisranges[i, 2] = tmp
                print("flipping {}".format(i))
        print(self.axisranges)

        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        ax.scatter(newcoords[:, 0], newcoords[:, 1], newcoords[:, 2])
        ax.scatter(endcoords[:, 0], endcoords[:, 1], endcoords[:, 2])
        plt.show()

        self.done(0)

    def handleGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        if self.captureNextCenter:
            self.captureNextCenter = False
            self.centerBuffer[:, self.centeri] = np.array([roll, pitch, yaw])
            self.centeri += 1

        if self.captureNextAxis is not None:
            self.axisEndBuffer[:, self.captureNextAxis] = np.array([roll, pitch, yaw])
            self.captureNextAxis = None

        if time.time() * 1000 >= self.nextSampleT:
            self.sampleBuffer[:, self.samplei] = np.array([roll, pitch, yaw])
            self.samplei += 1
            self.nextSampleT = time.time() * 1000 + self.TIME_BETWEEN_SAMPLE


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

        self.isLeftCalibrated = False
        self.isRightCalibrated = False

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
        print("Initiating calibration on side {}".format(side))
        self.leftCalibButton.setEnabled(False)
        self.rightCalibButton.setEnabled(False)

        self.calibDialog = CalibrationDialog(side)
        self.calibDialog.exec()
        self.leftCalibButton.setEnabled(True)
        self.rightCalibButton.setEnabled(True)
        if side == "L":
            self.isLeftCalibrated = True
            self.leftCalib = self.calibDialog
            fvnofl = (0.0, 1.0)
            fvflip = (1.0, 0.0)
            if self.leftCalib.axisranges[0, 0] < self.leftCalib.axisranges[0, 2]:
                fv = fvnofl
            else:
                fv = fvflip
            self.leftInterp0 = interp1d(self.leftCalib.axisranges[0, :], [
                                        0.0, 0.5, 1.0], fill_value=fv, bounds_error=False)
            if self.leftCalib.axisranges[1, 0] < self.leftCalib.axisranges[1, 2]:
                fv = fvnofl
            else:
                fv = fvflip
            self.leftInterp1 = interp1d(self.leftCalib.axisranges[1, :], [
                                        0.0, 0.5, 1.0], fill_value=fv, bounds_error=False)
            if self.leftCalib.axisranges[2, 0] < self.leftCalib.axisranges[2, 2]:
                fv = fvnofl
            else:
                fv = fvflip
            self.leftInterp2 = interp1d(self.leftCalib.axisranges[2, :], [
                                        0.0, 0.5, 1.0], fill_value=fv, bounds_error=False)
        else:
            self.isRightCalibrated = True
            self.rightCalib = self.calibDialog

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

        if self.isLeftCalibrated:
            c = np.array([roll, pitch, yaw]) - self.leftCalib.center
            t = self.leftCalib.ica.transform(c.reshape((1, -1)))[0, :]
            v = np.empty((3,))
            print("c {}".format(c))
            print("t {}".format(t))
            # raise Exception("replace with scipy")
            # v[0] = np.interp(t[0], self.leftCalib.axisranges[0, :], [0.0, 0.5, 1.0])
            # v[1] = np.interp(t[1], self.leftCalib.axisranges[1, :], [0.0, 0.5, 1.0])
            # v[2] = np.interp(t[2], self.leftCalib.axisranges[2, :], [0.0, 0.5, 1.0])
            v[0] = self.leftInterp0(t[0])
            v[1] = self.leftInterp1(t[1])
            v[2] = self.leftInterp2(t[2])

            self.lrval = v[self.leftCalib.axes[0]]
            self.lpval = v[self.leftCalib.axes[1]]
            self.lyval = v[self.leftCalib.axes[2]]
            print("rpy: {}, {}, {}".format(self.lrval, self.lpval, self.lyval))
        else:
            self.lrval = roll - self.lrcenter + 0.5
            if self.lrval > 1.0:
                self.lrval -= 1.0
            self.lpval = pitch - self.lpcenter + 0.5
            if self.lpval > 1.0:
                self.lpval -= 1.0
            self.lyval = yaw - self.lycenter + 0.5
            if self.lyval > 1.0:
                self.lyval -= 1.0

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

        self.rrval = np.interp(self.rrval, [self.rrminval, 0.5, self.rrmaxval], [0.0, 0.5, 1.0])
        self.rpval = np.interp(self.rpval, [self.rpminval, 0.5, self.rpmaxval], [0.0, 0.5, 1.0])
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
