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

    def __init__(self, plotOutput=False, publishOutput=True):
        super().__init__()
        self.publishOutput = publishOutput
        self.plotOutput = plotOutput

        self.packetSize = 32  # bytes
        self.FINGER_THUMB_CON = 1
        self.FINGER_PALM_CON = 2

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

        self.GYRO_MIN_DELAY = 50  # ms between gyro messages (independent between hands)
        self.last_lgyro_time = 0
        self.last_rgyro_time = 0

    def run(self):
        if not self._isconnected:
            r = self.connectToBoard()
            if r != 0:
                print("BoardInteractor couldn't connect to board, return val {}".format(r))

            self._isconnected = True

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
            readres = self.parseBoardMsg()
            if readres != 0:
                print("Reading from board failed with code {}, trying again in 1 second".format(readres))
                time.sleep(1)
                self._board.flushInput()
                self.alignSerialInput()
                continue
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

                        # hlen = self.HAPTIC_LEN_LONG
                        # if not self._connections[i]:
                        #     hlen = self.HAPTIC_LEN_SHORT
                        # self.setHaptic(self.motorForFinger(i), hlen)

                if time.time() * 1000 - self.last_lgyro_time > self.GYRO_MIN_DELAY:
                    if self._lroll != self._lroll_old or self._lpitch != self._lpitch_old or self._lyaw != self._lyaw_old:
                        pub.sendMessage('LGyro', roll=self._lroll, pitch=self._lpitch, yaw=self._lyaw,
                                        rollChanged=self._lroll != self._lroll_old, pitchChanged=self._lpitch != self._lpitch_old, yawChanged=self._lyaw != self._lyaw_old)
                        self._lroll_old = self._lroll
                        self._lpitch_old = self._lpitch
                        self._lyaw_old = self._lyaw
                        self.last_lgyro_time = time.time() * 1000

                if time.time() * 1000 - self.last_rgyro_time > self.GYRO_MIN_DELAY:
                    if self._rroll != self._rroll_old or self._rpitch != self._rpitch_old or self._ryaw != self._ryaw_old:
                        pub.sendMessage('RGyro', roll=self._rroll, pitch=self._rpitch, yaw=self._ryaw,
                                        rollChanged=self._rroll != self._rroll_old, pitchChanged=self._rpitch != self._rpitch_old, yawChanged=self._ryaw != self._ryaw_old)
                        self._rroll_old = self._rroll
                        self._rpitch_old = self._rpitch
                        self._ryaw_old = self._ryaw
                        self.last_rgyro_time = time.time() * 1000

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
            vals = np.array(struct.unpack(str(self.packetSize) +
                            'b', self._board.read(self.packetSize)))
            print(vals)
            if vals[-1] == 0 and vals[-2] == 1 and vals[-3] == 2 and vals[-4] == 3:
                break

            for i in range(len(vals)):
                if vals[i] == 3 and vals[(i+1) % len(vals)] == 2 and vals[(i+2) % len(vals)] == 1 and vals[(i+3) % len(vals)] == 0:
                    self._board.read(i + 4)
                    break

    def parseBoardMsg(self):
        dat = self._board.read(self.packetSize)
        while self._board.in_waiting >= self.packetSize:
            dat = self._board.read(self.packetSize)

        vals = struct.unpack('4b3f6h4b', dat)
        # vals = struct.unpack('bbbb4f', dat)
        # valtest = struct.unpack('bbbbfffbbbb', dat)
        if not (vals[-1] == 0 and vals[-2] == 1 and vals[-3] == 2 and vals[-4] == 3):
            print(vals)
            return 1
        gyrovals = np.array(vals[4:7])
        p = 3.1415926
        self._rroll = (gyrovals[2] + p/2.0) / (2.0*p)
        self._rpitch = (gyrovals[1] + p/2.0) / (2.0*p)
        self._ryaw = (gyrovals[0] + p/2.0) / (2.0*p)

        # print(self.plotVals)
        if self.plotOutput:
            self.plotVals = np.roll(self.plotVals, -1, axis=1)
            self.plotVals[0:3, -1] = gyrovals[0:3]
            # self.plotVals[3:6, -1] = vals[4:7]
            print(vals[7:13])

        self._connections = [False] * 16
        if vals[0] == 1:
            self._connections[Fingers['RIT'].value] = True
        elif vals[0] == 2:
            self._connections[Fingers['RIP'].value] = True
        elif vals[0] == 3:
            self._connections[Fingers['RIP'].value] = True
            self._connections[Fingers['RIT'].value] = True
        if vals[1] == 1:
            self._connections[Fingers['RMT'].value] = True
        elif vals[1] == 2:
            self._connections[Fingers['RMP'].value] = True
        elif vals[1] == 3:
            self._connections[Fingers['RMP'].value] = True
            self._connections[Fingers['RMT'].value] = True
        if vals[2] == 1:
            self._connections[Fingers['RRT'].value] = True
        elif vals[2] == 2:
            self._connections[Fingers['RRP'].value] = True
        elif vals[2] == 3:
            self._connections[Fingers['RRT'].value] = True
            self._connections[Fingers['RRP'].value] = True
        if vals[3] == 1:
            self._connections[Fingers['RPT'].value] = True
        elif vals[3] == 2:
            self._connections[Fingers['RPP'].value] = True
        elif vals[3] == 3:
            self._connections[Fingers['RPT'].value] = True
            self._connections[Fingers['RPP'].value] = True

        return 0

    def sendBoardHapticData(self):
        # TODO implement
        # Note if board read fails this is never called ... need to change for arduino to work properly?
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
