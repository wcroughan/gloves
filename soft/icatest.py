import numpy as np
from sklearn.decomposition import FastICA
import matplotlib.pyplot as plt

npa = 10
a = np.zeros((3, npa*3))

ii = 0
for ai in range(3):
    for wai in range(npa):
        a[ai, ii] = wai - npa / 2
        ii += 1

ica = FastICA()
newcoords = ica.fit_transform(a.T)
print(newcoords)

p = np.eye(3) * 7
pt = ica.transform(p)

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
# ax.scatter(a[0, :], a[1, :], a[2, :])
ax.scatter(newcoords[:, 0], newcoords[:, 1], newcoords[:, 2])
ax.scatter(pt[:, 0], pt[:, 1], pt[:, 2])
plt.show()
