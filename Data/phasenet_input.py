#!/bin/python -w
# coding: utf-8

# Import modules
import math
import numpy as np
import pandas as pd
import os
import shutil
from time import time
import obspy
from obspy.geodetics import locations2degrees
from datetime import datetime, timedelta, timezone
from obspy import UTCDateTime, read, read_inventory, read_events
from obspy.clients.fdsn import Client

# Date and time 
year0 = 2016 # year
mon0 = 10 # month
day0 = 14 #day
nday = 1 # number of days
tbeg = 0 # beginning time
         # the length will be as long as the data in waveform_sac

# Station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
threecomp = 1 # 1: use three components E/N/Z
              # 0: use E/N/Z, E/Z, N/Z, Z
              # It is fine to use either one before the dt.cc calculation.
              # NOTE: FDTCC use ENZ only by default. 
              #       Want to use Z alone? change E and N to Z in FDTCC.c.

data_dir = os.getcwd()
sac_waveform_dir = os.path.join(data_dir, "waveform_sac")
stationdir = os.path.join(data_dir,"station_all.dat")
stationsel = os.path.join(data_dir,"station.dat")

fname = os.path.join(data_dir,"fname.csv")
p = open(stationsel,"w")
o = open(fname,"w")
o.write('fname\n')

if not os.path.isdir(sac_waveform_dir):
    print("No this directory ",sac_waveform_dir)

for i in range(nday):
    origins = UTCDateTime(year0,mon0,day0) + 86400*i
    newdate = origins.strftime("%Y/%m/%d")
    year,mon,day = newdate.split('/')
    print(year,mon,day)
    sacid_dir = os.path.join(sac_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))
        
    with open(stationdir, "r") as f:
        for station in f:
            lon, lat, net, sta, chan, elev = station.split(" ")
        
            chane = chan[:2]+"E" #E,2
            chann = chan[:2]+"N" #N,1 consider use st.rotate in waveform_download_mseed.py
            chanz = chan[:2]+"Z"

            tracee = os.path.join(sacid_dir,net+'.'+sta+'.'+chane)
            tracen = os.path.join(sacid_dir,net+'.'+sta+'.'+chann)
            tracez = os.path.join(sacid_dir,net+'.'+sta+'.'+chanz)
            
            dist = 111.19*locations2degrees(float(latref), float(lonref), float(lat), float(lon))
            if dist > maxradius:
                continue
         
            if os.path.exists(tracee) or os.path.exists(tracen) or os.path.exists(tracez):
                o.write('{}\n'.format(year+mon+day+'/'+net+'.'+sta+'.'+chanz[:-1]+"*"))
                p.write(station)

o.close()
f.close()
p.close()

os.system ("cat {} | sort -u -k 4 | uniq > uniq_st.dat && mv uniq_st.dat {}".format (stationsel, stationsel))
