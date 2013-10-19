import pygeode as pyg
import numpy as np
#import pylab as pyl
#from pygeode.formats import netcdf as nc

def buildT1():
  lat = pyg.gausslat(32)
  lat = pyg.Lat(np.linspace(-90, 90, 31))
  lon = pyg.Lon(np.arange(0, 360, 360/60.))

  T_c = 260. + 40. * pyg.exp(-(lat/45.)**2)
  T_wave = 0.05 * lat * pyg.sind(6*lon)
  T = T_c + T_wave
  T.name = 'Temp'
  T.plotatts['plottitle'] = 'Temp'

  return pyg.Dataset([T], atts={'history':'Synthetic Temperature data generated by pygeode'})

def buildT2():
  nyrs = 10
  lat = pyg.gausslat(32)
  lon = pyg.Lon(np.arange(0, 360, 360/64.))
  time = pyg.ModelTime365(values=np.arange(nyrs*365), \
          units='days', startdate={'year':2011, 'month':1, 'day':1})
  pres = pyg.Pres(np.arange(1000, 0, -50.))
  z = 6.6 * pyg.log(1000./pres)

  ts1 = 2*pyg.sin(2*np.pi*time/365.) + 4*pyg.Var((time,), values=np.random.randn(nyrs*365))
  ts1 = ts1.smooth('time', 20)
  ts2 = -5 + 0.6*time/365. + 5*pyg.Var((time,), values=np.random.randn(nyrs*365))
  ts2 = ts2.smooth('time', 20)

  T_c = 260. + 40. * pyg.exp(-((lat - 10*np.sin(2*np.pi*time/365))/45.)**2)
  T_wave = 0.05 * lat * pyg.sind(6*lon - time)# * ts1
  T_lapse = -5*z

  Tf = (T_lapse + T_c + T_wave).transpose('time', 'pres', 'lat', 'lon')
  Tf.name = 'Temp'
  Tf.plotatts['plottitle'] = 'Temp'

  U_c = 40 * pyg.sind(2*lat)**2 * pyg.sin(2*np.pi * z / 12)**2
  U_wave = 0.08 * lat * pyg.sind(6*lon - time)
  U = (U_c + ts2*U_wave).transpose('time', 'pres', 'lat', 'lon')
  U.name = 'U'
  U.plotatts['plottitle'] = 'U'
  return pyg.Dataset([Tf, U], atts={'history':'Synthetic Temperature and Wind data generated by pygeode'})

t1 = buildT1()
t2 = buildT2()

