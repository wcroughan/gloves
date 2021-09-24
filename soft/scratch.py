import numpy as np
import matplotlib.pyplot as plt

fname = "./calibSample.npz"
dat = np.load(fname)
print(dat.files)
print(dat['samples'])

plt.plot(dat['samples'].T)
plt.show()
