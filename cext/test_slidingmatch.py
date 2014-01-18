import numpy as n
from tests import buildnload

cm = buildnload('slidingmatch')

print cm.__file__
print dir(cm)

dat = n.random.randn(5)
tem = n.random.randn(5, 5)
qf1 = n.dot(dat, n.dot(tem, dat))
print n.dot(tem, dat)
print qf1, type(qf1)

qf2 = float(cm.qform(dat, tem))
print qf2, type(qf2)

sigma = n.array([[.3, -1, 1],
                 [-1, .2, -1],
                 [1, -1, .1]])
mu = n.array([.2, -.5, 1])
off = n.array([1, 5, 9])


def gmatch(stim, mean, cov, offsets):
    resp = n.zeros_like(stim)
    icov = cov
    for i in range(offsets.max(), stim.size):
        v = stim[i - offsets] - mean
        if i == 40:
            print v
            print offsets
            print mean
        resp[i] = n.dot(v, n.dot(icov, v))
    return resp


os = n.array([0, 2, 3, 4, 5])
dat2 = n.random.randn(500)
m = n.array([-1.0, 0])
c = n.array([[3.0, 2.0], [2.0, 3.0]])
o = n.array([20, 26])
print("-------")
z = cm.sgauss(dat2, m, c, o)
print z[40:100]

z2 = gmatch(dat2, m, c, o)
print z2[40:100]
