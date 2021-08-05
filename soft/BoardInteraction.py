from pubsub import pub
import numpy as np
from enum import Enum

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


class BoardInteractor(ThreadExtension.StoppableThread):
    """
    Reads messages from the board and interprets them.
    Other objects can query for specific values or set up custom alerts
    """

    # MAIN LIFECYCLE

    def __init__(self):
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

        self._isconnected = False

    def run(self):
        if not self._isconnected:
            r = self.connectToBoard()
            if r != 0:
                print("BoardInteractor couldn't connect to board, return val {}".format(r))

            self._isconnected = True

        # TODO clear any built up serial messages

        while not self.req_stop():
            self.parseBoardMsg()

            for i in range(len(self._connections)):
                if self._connections_old[i] != self._connections[i]:
                    self._connections_old[i] = self._connections[i]
                    fname = Fingers(i).name
                    pub.sendMessage('FingerConnection', con=self._connections[i], finger=fname)

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
        raise Exception("UNimplemented")

    def parseBoardMsg(self):
        # TODO read values, use numpy to linearly scale 0.0-1.0 on range defined in calibration step
        raise Exception("UNimplemented")

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
