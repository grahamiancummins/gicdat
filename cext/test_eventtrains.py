import numpy as n
from tests import buildnload
cm = buildnload('eventtrains')

print cm.__file__
print dir(cm)


st1 = (1, 20, 75, 150)
st2 = (25, 80, 149)
st3 = (25, 120, 200)

print cm.vpdist(st1, st2, 0)
print cm.vpdist(st1, st2, .05)
print cm.vpdist(st1, st2, 2)

d = cm.vpdistMatrix((st1, st2, st3, (), ()), .05)
print d
print cm.vpdist((), (111900, 113000, 114725), .001)

d = cm.vpdistSet((st1, st2, st3, ()), (st1, st2, ()), .05)
print d
