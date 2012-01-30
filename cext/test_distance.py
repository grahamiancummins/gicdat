import numpy as n
from tests import buildnload
cm = buildnload('distance')

print cm.__file__
print dir(cm)

z = n.random.randn(5,3)
print(z)
print cm.edist(z)
print cm.cbdist(z)

