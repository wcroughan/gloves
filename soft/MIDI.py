from pubsub import pub

from BoardInteraction import BoardInteractor, Fingers
from ThreadExtension import StoppableThread


class BoardToMIDI(StoppableThread):
    def __init__(self):
        pub.subscribe(self.handleFingerConnection, 'FingerConnection')
        pub.subscribe(self.handleLGyroData, 'LGyro')
        pub.subscribe(self.handleRGyroData, 'RGyro')

        self._b = BoardInteractor()

    def run(self):
        self._b.start()

        cmd = None
        while cmd is None:
            cmd = input("input q to quit:")

        self._b.stop()

    def handleFingerConnection(self, con, finger):
        if finger == "LIT":
            if con:
                self.startNote()
            else:
                self.stopNote()

    def handleLGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        pass

    def handleRGyroData(self, roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
        pass

    def startNote(self):
        pass

    def stopNote(self):
        pass


if __name__ == "__main__":
    goGoMIDI()
