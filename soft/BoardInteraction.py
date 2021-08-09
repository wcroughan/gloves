from pubsub import pub
import numpy as np
from enum import Enum
import time
import serial
import struct
import matplotlib.pyplot as plt

import ThreadExtension


class Fingers(Enum):
    LIT = 0
    LMT = 1
    LRT = 2
    LPT = 3
    LIP = 4
    LMP = 5
    LRP = 6
    LPP = 7
    RIT = 8
    RMT = 9
    RRT = 10
    RPT = 11
    RIP = 12
    RMP = 13
    RRP = 14
    RPP = 15


class HapticMotors(Enum):
    # Each hand has a palm and thumb indiator, and left, middle, and right indicator on top
    LT = 0
    LP = 1
    LL = 2
    LM = 3
    LR = 4
    RT = 5
    RP = 6
    RL = 7
    RM = 8
    RR = 9


class BoardInteractor(ThreadExtension.StoppableThread):
    """
    Reads messages from the board and interprets them.
    Other objects can query for specific values or set up custom alerts
    """

    # CONSTANTS
    HAPTIC_LEN_LONG = 0.3
    HAPTIC_LEN_SHORT = 0.1

    # MAIN LIFECYCLE

    def __init__(self, plotOutput=False, publishOutput=True, runCalibration=False):
        super().__init__()
        self.publishOutput = publishOutput
        self.plotOutput = plotOutput
        self.runCalibration = runCalibration
        self.offsets = [0] * 4

        self._lroll = 0.0
        self._lpitch = 0.0
        self._lyaw = 0.0
        self._rroll = 0.0
        self._rpitch = 0.0
        self._ryaw = 0.0
        self._connections = [False] * 16

        self._lroll_old = 0.0
        self._lpitch_old = 0.0
        self._lyaw_old = 0.0
        self._rroll_old = 0.0
        self._rpitch_old = 0.0
        self._ryaw_old = 0.0
        self._connections_old = [False] * 16

        self.haptic_state = [False] * 10
        self.haptic_off_time = [0] * 10

        self._isconnected = False

        self.plotLen = 30
        self.plotVals = np.zeros((3, self.plotLen))

    def run(self):
        if not self._isconnected:
            r = self.connectToBoard()
            if r != 0:
                print("BoardInteractor couldn't connect to board, return val {}".format(r))

            self._isconnected = True

        if self.runCalibration:
            self.calibrateBoard()

        if self.plotOutput:
            plt.ion()
            self.fig = plt.figure()
            self.ax = self.fig.add_subplot(1, 1, 1)
            self.ax.set_ylim(-2*3.14159, 2*3.14159)
            self.ls = []
            for i in range(3):
                l, = self.ax.plot(self.plotVals[i, :])
                l.set_label(str(i))
                self.ls.append(l)

            self.ax.legend(loc='lower left')

        while not self.req_stop():
            self.parseBoardMsg()
            self.sendBoardHapticData()

            if self.plotOutput:
                for i in range(3):
                    self.ls[i].set_ydata(self.plotVals[i, :])
                    plt.pause(.01)
                    # self.ax.relim()
                    # self.ax.autoscale_view()

            if self.publishOutput:
                for i in range(len(self._connections)):
                    if self._connections_old[i] != self._connections[i]:
                        self._connections_old[i] = self._connections[i]
                        fname = Fingers(i).name
                        pub.sendMessage('FingerConnection', con=self._connections[i], finger=fname)

                        hlen = self.HAPTIC_LEN_LONG
                        if not self._connections[i]:
                            hlen = self.HAPTIC_LEN_SHORT
                        self.setHaptic(self.motorForFinger(i), hlen)

                if self._lroll != self._lroll_old or self._lpitch != self._lpitch_old or self._lyaw != self._lyaw_old:
                    pub.sendMessage('LGyro', roll=self._lroll, pitch=self._lpitch, yaw=self._lyaw,
                                    rollChanged=self._lroll != self._lroll_old, pitchChanged=self._lpitch != self._lpitch_old, yawChanged=self._lyaw != self._lyaw_old)
                    self._lroll_old = self._lroll
                    self._lpitch_old = self._lpitch
                    self._lyaw_old = self._lyaw

                if self._rroll != self._rroll_old or self._rpitch != self._rpitch_old or self._ryaw != self._ryaw_old:
                    pub.sendMessage('RGyro', roll=self._rroll, pitch=self._rpitch, yaw=self._ryaw,
                                    rollChanged=self._rroll != self._rroll_old, pitchChanged=self._rpitch != self._rpitch_old, yawChanged=self._ryaw != self._ryaw_old)
                    self._rroll_old = self._rroll
                    self._rpitch_old = self._rpitch
                    self._ryaw_old = self._ryaw

    # COMMUNICATION FUNCTIONS WITH BOARD
    def connectToBoard(self):
        try:
            self._board = serial.Serial(port="/dev/ttyACM0", baudrate=115200)
        except:
            self._board = serial.Serial(port="COM9", baudrate=115200)

        print("board: {}".format(self._board))
        if self._board is None:
            return 1
        else:
            self.alignSerialInput()
            return 0

    def alignSerialInput(self):
        print("Aligning serial input")
        while True:
            vals = np.array(struct.unpack('16b', self._board.read(16)))
            if vals[-1] == 0 and vals[-2] == 1 and vals[-3] == 2 and vals[-4] == 3:
                break
            # print(vals)
            # if np.count_nonzero(vals) == len(vals) - 4 and vals[-1] == 0 and vals[-2] == 0 and vals[-3] == 0 and vals[-4] == 0:
            #     break
            # vals = np.array(struct.unpack('4f', self._board.read(16)))
            print(vals)
            # if np.count_nonzero(vals) == len(vals) - 1 and vals[-1] == 0:
            # break
            # if np.count_nonzero(vals) == len(vals) - 1:
            #     for i in range(len(vals)):
            #         self._board.read(4)
            #         if vals[i] == 0:
            #             break
            # else:
            #     self._board.read(1)
            self._board.read(1)

    def calibrateBoard(self):
        print("Calibrating, hold still!")
        NUM_CALIB_PASSES = 5
        self._board.flushInput()
        offs = np.zeros((4, NUM_CALIB_PASSES))
        for i in range(NUM_CALIB_PASSES):
            vals = struct.unpack('4f', self._board.read(16))
            assert vals[-1] == 0
            print(vals, offs)
            offs[:, i] = np.array(vals)

        self.offsets = np.mean(offs, axis=1)

    def parseBoardMsg(self):
        # TODO use numpy to linearly scale 0.0-1.0 on range defined in calibration step
        # TODO Read from other board also
        dat = self._board.read(16)
        while self._board.in_waiting >= 16:
            dat = self._board.read(16)
        vals = struct.unpack('4f', dat)
        valtest = struct.unpack('fffbbbb', dat)
        if not (valtest[-1] == 0 and valtest[-2] == 1 and valtest[-3] == 2 and valtest[-4] == 3):
          print(valtest)
        vals = np.array(vals) - self.offsets
        # print(vals)
        p = 3.1415926
        self._rroll = (vals[2] + p/2.0) / (2.0*p)
        self._rpitch = (vals[1] + p/2.0) / (2.0*p)
        self._ryaw = (vals[0] + p/2.0) / (2.0*p)
        # self._rroll = vals[4]
        # self._rpitch = vals[5]
        # self._ryaw = vals[6]

        # print(self.plotVals)
        if self.plotOutput:
            self.plotVals = np.roll(self.plotVals, -1, axis=1)
            self.plotVals[0:3, -1] = vals[0:3]
            # self.plotVals[3:6, -1] = vals[4:7]

    def sendBoardHapticData(self):
        # TODO
        pass

    def setHaptic(self, motor, length, turnOn=True):
        self.haptic_state[motor] = turnOn
        self.haptic_off_time[motor] = max(self.haptic_off_time[motor], time.time()+length)

    def motorForFinger(self, finger):
        ret = HapticMotors[finger[0] + finger[2]]
        print("in {}, out {}".format(finger, ret))
        return ret

    # BASIC GETTERS
    def getLRoll(self):
        return self._lroll

    def getLPitch(self):
        return self._lpitch

    def getLYaw(self):
        return self._lyaw

    def getRRoll(self):
        return self._rroll

    def getRPitch(self):
        return self._rpitch

    def getRYaw(self):
        return self._ryaw


if __name__ == "__main__":
    bi = BoardInteractor(plotOutput=True, publishOutput=False)
    bi.run()
    input("press enter to stop")
    bi.stop()
