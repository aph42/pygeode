
import plot_wr_ph as pl, plot_sc_ph as pygpl
import numpy as np
import pylab as pyl
import pygeode as pyg
from pygeode.tutorial import t1

reload(pl)
reload(pygpl)

lv = np.arange(240, 310, 2)
ln = np.arange(240, 310, 10)
Ax = pygpl.contour(t1.Temp, lv, ln)
Ax.drawcoastlines()
Ax.drawmeridians([0, 60, 120, 180, 240, 300])
Ax.drawparallels([-50, 0, 50])

#pl.save(Ax, 'test_ph3.fig')
#Ax = pl.load('test_ph3.fig')
Ax.render(1)
