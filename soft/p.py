import matplotlib.pyplot as plt
import time
import numpy as np

plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111)

ydat = np.array([])
l, = ax.plot(ydat)
# plt.show()

for i in range(100):
    ydat = np.concatenate((ydat, np.array([i])), axis=0)
    print(ydat)
    l.set_data(ydat, ydat)
    ax.relim()
    ax.autoscale_view()
    # fig.canvas.draw()
    plt.pause(.01)
    # time.sleep(1)
