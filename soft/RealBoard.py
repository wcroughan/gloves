from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QGridLayout, QButtonGroup, QRadioButton
from PyQt5.QtCore import Qt, QTimer
from pubsub import pub

from BoardInteraction import BoardInteractor


class RealBoard(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.allfingers = ["LP", "LR", "LM", "LI", "RI", "RM", "RR", "RP"]
        self.initUI()
        self.connectToBoard()

    def initUI(self):
        layout = QVBoxLayout()

        self.fingerDict = dict()

        g1 = QGridLayout()
        g1.addWidget(QLabel("Thumb"), 1, 0)
        g1.addWidget(QLabel("Palm"), 2, 0)
        for fi, f in enumerate(self.allfingers):
            g1.addWidget(QLabel(f), 0, fi+1)

            tmombtn = QPushButton("Off")
            tmombtn.setEnabled(False)
            self.fingerDict[f + "T"] = tmombtn
            tmombtn.setStyleSheet('QPushButton {background-color: white; border:  none}')
            g1.addWidget(tmombtn, 1, fi+1)

            pmombtn = QPushButton("Off")
            pmombtn.setEnabled(False)
            self.fingerDict[f + "P"] = pmombtn
            pmombtn.setStyleSheet('QPushButton {background-color: white; border:  none}')
            g1.addWidget(pmombtn, 2, fi+1)

        layout.addLayout(g1)

        self.gyroDict = dict()
        g2 = QGridLayout()
        axes = ["Roll", "Pitch", "Yaw"]
        sides = ["Left", "Right"]
        for si, s in enumerate(sides):
            for ai, ax in enumerate(axes):
                g2.addWidget(QLabel(s + ax), ai, si*2)
                vallbl = QLabel("?")
                self.gyroDict[s[0] + ax[0]] = vallbl
                g2.addWidget(vallbl, ai, si*2+1)

        layout.addLayout(g2)

        self.setLayout(layout)

    def connectToBoard(self):
        self.board = BoardInteractor()
        self.board.start()

        pub.subscribe(self.handleFingerConnection, 'FingerConnection')
        pub.subscribe(self.handleLGyroData, 'LGyro')
        pub.subscribe(self.handleRGyroData, 'RGyro')

    def closeEvent(self, event):
        if self.board is not None:
            self.board.stop()
        print("stopping board comms")
        super().closeEvent(event)

    def handleFingerConnection(self, con, finger):
        if con:
            self.fingerDict[finger].setStyleSheet(
                'QPushButton {background-color: blue; border:  none}')
        else:
            self.fingerDict[finger].setStyleSheet(
                'QPushButton {background-color: white; border:  none}')

    def handleLGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        self.gyroDict["LR"].setText(str(roll))
        self.gyroDict["LP"].setText(str(pitch))
        self.gyroDict["LY"].setText(str(yaw))

    def handleRGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        self.gyroDict["RR"].setText(str(roll))
        self.gyroDict["RP"].setText(str(pitch))
        self.gyroDict["RY"].setText(str(yaw))
