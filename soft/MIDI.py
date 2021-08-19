from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QComboBox
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, CONTROL_CHANGE, PITCH_BEND


class MIDIMapping:
    def __init__(self, midiport):
        self.midiport = midiport
        self.widget = QWidget()

    def rightRollChanged(self, val):
        pass

    def rightPitchChanged(self, val):
        pass

    def rightYawChanged(self, val):
        pass

    def leftRollChanged(self, val):
        pass

    def leftPitchChanged(self, val):
        pass

    def leftYawChanged(self, val):
        pass

    def fingerConnection(self, finger, con):
        pass

    def startNote(self, pitch=60, vel=112):
        self.midiport.send_message([NOTE_ON, pitch, vel])

    def stopNote(self, pitch=60):
        self.midiport.send_message([NOTE_OFF, pitch, 0])

    def cc(self, cc=0, value=0):
        if value < 0:
            # print("Correcting cc value {} to 0".format(value))
            value = 0
        if value > 127:
            # print("Correcting cc value {} to 127".format(value))
            value = 127
        self.midiport.send_message([CONTROL_CHANGE, cc, value])

    def pb(self, value=8192):
        self.midiport.send_message([PITCH_BEND, value & 0x7f, (value >> 7) & 0x7f])


class M1(MIDIMapping):
    def __init__(self, midiport):
        super().__init__(midiport)

        self.rr_ccnum = 22
        self.rp_ccnum = 23
        self.ry_ccnum = 24
        self.rr_enabled = True
        self.rp_enabled = True
        self.ry_enabled = True

        self.lr_ccnum = 25
        self.lp_ccnum = 26
        self.ly_ccnum = 27
        self.lr_enabled = True
        self.lp_enabled = True
        self.ly_enabled = True

        self.initWidget()

    def initWidget(self):
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
        self.lrvalLabel = QLabel("0")
        l4.addWidget(QLabel("Value:"))
        l4.addWidget(self.lrvalLabel)
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
        self.lpvalLabel = QLabel("0")
        l5.addWidget(QLabel("Value:"))
        l5.addWidget(self.lpvalLabel)
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
        self.lyvalLabel = QLabel("0")
        l6.addWidget(QLabel("Value:"))
        l6.addWidget(self.lyvalLabel)
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

    def rightRollChanged(self, val):
        self.rrvalLabel.setText(str(int(val*127)))
        if self.rr_enabled:
            self.cc(self.rr_ccnum, int(val*127))

    def rightPitchChanged(self, val):
        self.rpvalLabel.setText(str(int(val*127)))
        if self.rp_enabled:
            self.cc(self.rp_ccnum, int(val*127))

    def rightYawChanged(self, val):
        self.ryvalLabel.setText(str(int(val*127)))
        if self.ry_enabled:
            self.cc(self.ry_ccnum, int(val*127))

    def leftRollChanged(self, val):
        self.lrvalLabel.setText(str(int(val*127)))
        if self.lr_enabled:
            self.cc(self.lr_ccnum, int(val*127))

    def leftPitchChanged(self, val):
        self.lpvalLabel.setText(str(int(val*127)))
        if self.lp_enabled:
            self.cc(self.lp_ccnum, int(val*127))

    def leftYawChanged(self, val):
        self.lyvalLabel.setText(str(int(val*127)))
        if self.ly_enabled:
            self.cc(self.ly_ccnum, int(val*127))


class ToyMidiMap(MIDIMapping):
    def __init__(self, midiport):
        super().__init__(midiport)

        self.rootNote = 60
        self.SCALE_MODES = ["Major Pentatonic", "Minor Pentatonic",
                            "Major", "Minor", "Mixolydian", "Blues"]
        self.setScaleMode(0)

        self.leftNoteVelocity = 127
        self.rightNoteVelocity = 127

        self.rr_ccnum = 22
        self.rp_ccnum = 23
        self.ry_ccnum = 24
        self.rr_enabled = True
        self.rp_enabled = True
        self.ry_enabled = True

        self.lr_ccnum = 25
        self.lp_ccnum = 26
        self.ly_ccnum = 27
        self.lr_enabled = True
        self.lp_enabled = True
        self.ly_enabled = True

        self.VELOCITY_CONTROL_OPTIONS = ["Right Pitch", "Right Roll",
                                         "Right Yaw", "Left Pitch", "Left Roll", "Left Yaw", "127"]
        self.lvelctrl = 6
        self.rvelctrl = 6

        self.initWidget()

    def initWidget(self):
        layout = QVBoxLayout()

        lh = QHBoxLayout()
        lh.addWidget(QLabel("Root note:"))
        rns = QSpinBox()
        rns.setMaximum(127)
        rns.setValue(self.rootNote)
        rns.valueChanged.connect(self.setRootNote)
        lh.addWidget(rns)
        self.rootNoteNameLabel = QLabel(self.noteNameForVal(self.rootNote))
        lh.addWidget(self.rootNoteNameLabel)
        lh.addWidget(QLabel("Scale:"))
        scb = QComboBox()
        scb.addItems(self.SCALE_MODES)
        scb.currentIndexChanged.connect(self.setScaleMode)
        lh.addWidget(scb)
        layout.addLayout(lh)

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

        l7 = QHBoxLayout()
        l7.addWidget(QLabel("Right Velocity Control"))
        self.rvcb = QComboBox()
        self.rvcb.addItems(self.VELOCITY_CONTROL_OPTIONS)
        self.rvcb.currentIndexChanged.connect(
            lambda idx: self.velocityControlState("r", self.rvcb, idx))
        l7.addWidget(self.rvcb)
        layout.addLayout(l7)

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
        self.lrvalLabel = QLabel("0")
        l4.addWidget(QLabel("Value:"))
        l4.addWidget(self.lrvalLabel)
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
        self.lpvalLabel = QLabel("0")
        l5.addWidget(QLabel("Value:"))
        l5.addWidget(self.lpvalLabel)
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
        self.lyvalLabel = QLabel("0")
        l6.addWidget(QLabel("Value:"))
        l6.addWidget(self.lyvalLabel)
        layout.addLayout(l6)

        l8 = QHBoxLayout()
        l8.addWidget(QLabel("Left Velocity Control"))
        self.lvcb = QComboBox()
        self.lvcb.addItems(self.VELOCITY_CONTROL_OPTIONS)
        self.lvcb.currentIndexChanged.connect(
            lambda idx: self.velocityControlState("l", self.lvcb, idx))
        l8.addWidget(self.lvcb)
        layout.addLayout(l8)

        self.widget.setLayout(layout)

    def noteNameForVal(self, val):
        noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        q, r = divmod(val, 12)
        n1 = noteNames[r]
        n2 = q - 2
        ret = str(n1) + str(n2)
        return ret

    def setRootNote(self, val):
        self.rootNote = val
        self.rootNoteNameLabel.setText(self.noteNameForVal(val))

    def setScaleMode(self, idx):
        self.scale_mode = self.SCALE_MODES[idx]

        if self.scale_mode == "Major Pentatonic":
            self.scaleOffsets = [0, 2, 4, 7, 9, 12, 14, 16,
                                 24, 26, 28, 31, 33, 36, 38, 40]
        elif self.scale_mode == "Minor Pentatonic":
            self.scaleOffsets = [0, 3, 5, 7, 10, 12, 15, 17,
                                 24, 27, 29, 31, 34, 36, 39, 41]
        elif self.scale_mode == "Major":
            self.scaleOffsets = [0, 2, 4, 5, 7, 9, 11, 12,
                                 24, 26, 28, 29, 31, 31, 33, 36]
        elif self.scale_mode == "Minor":
            self.scaleOffsets = [0, 2, 3, 5, 7, 8, 10, 12,
                                 24, 26, 27, 29, 31, 30, 32, 36]
        elif self.scale_mode == "Mixolydian":
            self.scaleOffsets = [0, 2, 4, 5, 7, 9, 10, 12,
                                 24, 26, 28, 29, 31, 31, 32, 36]
        elif self.scale_mode == "Blues":
            self.scaleOffsets = [0, 3, 5, 6, 7, 10, 12, 15,
                                 24, 27, 29, 30, 31, 34, 36, 39]

    def fingerConnection(self, finger, con):
        noteidx = self.getNoteIdxForFingerName(finger)
        noteval = self.getNoteValForNoteIdx(noteidx)
        if con:
            vel = self.leftNoteVelocity
            if finger[0] == "R":
                vel = self.rightNoteVelocity
            self.startNote(pitch=noteval, vel=vel)
        else:
            self.stopNote(pitch=noteval)

    def getNoteIdxForFingerName(self, finger):
        ret = 0
        if finger[0] == "R":
            ret += 8

        if finger[2] == "P":
            ret += 4

        if finger[1] == "M":
            ret += 1
        elif finger[1] == "R":
            ret += 2
        elif finger[1] == "P":
            ret += 3

        return ret

    def getNoteValForNoteIdx(self, idx):
        return self.rootNote + self.scaleOffsets[idx]

    def rightRollChanged(self, val):
        self.rrvalLabel.setText(str(int(val*127)))
        if self.rr_enabled:
            self.cc(self.rr_ccnum, int(val*127))

        if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "Right Roll":
            self.leftNoteVelocity = int(val*127)
        if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "Right Roll":
            self.rightNoteVelocity = int(val*127)

    def rightPitchChanged(self, val):
        self.rpvalLabel.setText(str(int(val*127)))
        if self.rp_enabled:
            self.cc(self.rp_ccnum, int(val*127))

        if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "Right Pitch":
            self.leftNoteVelocity = int(val*127)
        if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "Right Pitch":
            self.rightNoteVelocity = int(val*127)

    def rightYawChanged(self, val):
        self.ryvalLabel.setText(str(int(val*127)))
        if self.ry_enabled:
            self.cc(self.ry_ccnum, int(val*127))

        if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "Right Yaw":
            self.leftNoteVelocity = int(val*127)
        if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "Right Yaw":
            self.rightNoteVelocity = int(val*127)

    def leftRollChanged(self, val):
        self.lrvalLabel.setText(str(int(val*127)))
        if self.lr_enabled:
            self.cc(self.lr_ccnum, int(val*127))

        if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "Left Roll":
            self.leftNoteVelocity = int(val*127)
        if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "Left Roll":
            self.rightNoteVelocity = int(val*127)

    def leftPitchChanged(self, val):
        self.lpvalLabel.setText(str(int(val*127)))
        if self.lp_enabled:
            self.cc(self.lp_ccnum, int(val*127))

        if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "Left Pitch":
            self.leftNoteVelocity = int(val*127)
        if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "Left Pitch":
            self.rightNoteVelocity = int(val*127)

    def leftYawChanged(self, val):
        self.lyvalLabel.setText(str(int(val*127)))
        if self.ly_enabled:
            self.cc(self.ly_ccnum, int(val*127))

        if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "Left Yaw":
            self.leftNoteVelocity = int(val*127)
        if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "Left Yaw":
            self.rightNoteVelocity = int(val*127)

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

    def velocityControlState(self, side, cb, idx):
        if side == "l":
            self.lvelctrl = idx
            if self.VELOCITY_CONTROL_OPTIONS[self.lvelctrl] == "127":
                self.leftNoteVelocity = 127
        elif side == "r":
            self.rvelctrl = idx
            if self.VELOCITY_CONTROL_OPTIONS[self.rvelctrl] == "127":
                self.rightNoteVelocity = 127
