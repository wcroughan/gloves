from pubsub import pub

from BoardInteraction import BoardInteractor


def printFingerConnection(con, finger):
    print("finger: {} -> {}".format(finger, con))


def printGyroDataOnlyChange(roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
    if rollChanged:
        print("roll: {}".format(roll))
    if pitchChanged:
        print("pitch: {}".format(pitch))
    if yawChanged:
        print("yaw: {}".format(yaw))


def printGyroDataAll(roll, pitch, yaw, rollChanged, pitchChanged, yawChanged):
    print("roll: {}\tpitch: {}\tyaw: {}".format(roll, pitch, yaw))


def printDataToConsole():
    pub.subscribe(printFingerConnection, 'FingerConnection')
    pub.subscribe(printGyroDataAll, 'LGyro')
    pub.subscribe(printGyroDataAll, 'RGyro')
    # pub.subscribe(printGyroDataOnlyChange, 'LGyro')
    # pub.subscribe(printGyroDataOnlyChange, 'RGyro')

    b = BoardInteractor()
    b.start()

    input("Press Enter to stop")
    b.stop()


if __name__ == "__main__":
    printDataToConsole()
