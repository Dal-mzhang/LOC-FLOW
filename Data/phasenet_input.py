#!/usr/bin/env python
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
dayleng = 3000 # seconds in one day
#dayleng = 86400 # seconds in one day

# Station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
numberofcomp = 3 # 1: use either Z or E,N,Z (PhaseNet works for either one)
                 # 3: use E,N,Z (STA/LTA requires three components)
                 #    current FDTCC requires two horizontal components to calculate dtcc for S phase pairs

data_dir = os.getcwd()
sac_waveform_dir = os.path.join(data_dir, "waveform_sac")
processed_waveform_dir = os.path.join(data_dir, "waveform_phasenet")
stationdir = os.path.join(data_dir,"station_all.dat")
stationsel = os.path.join(data_dir,"station.dat")

fname = os.path.join(data_dir,"fname.csv")
p = open(stationsel,"w")
o = open(fname,"w")
o.write('fname\n')

if not os.path.isdir(sac_waveform_dir):
    print("No this directory ",sac_waveform_dir)

if os.path.isdir(processed_waveform_dir):
    shutil.rmtree(processed_waveform_dir)
os.mkdir(processed_waveform_dir)

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
            
            if not os.path.exists(tracez):
                continue

            if os.path.exists(tracee) and os.path.exists(tracen) and os.path.exists(tracez):
            
                meta = obspy.Stream()
            
                # Although PhaseNet was trained using raw data without filtering,
                # highpass filtered waveforms have a better performace.
                tre = read(tracee)
                tre.detrend('demean')
                tre.detrend('linear')
                tre.filter(type="highpass",freq=1.0,zerophase=False)
            
                trn = read(tracen)
                trn.detrend('demean')
                trn.detrend('linear')
                trn.filter(type="highpass",freq=1.0,zerophase=False)
            
                trz = read(tracez)
                trz.detrend('demean')
                trz.detrend('linear')
                trz.filter(type="highpass",freq=1.0,zerophase=False)
            
                meta = tre + trn + trz
            else:
                
                if numberofcomp == 1:
                    meta = obspy.Stream()

                    trz = read(tracez)
                    trz.detrend('demean')
                    trz.detrend('linear')
                    trz.filter(type="highpass",freq=1.0,zerophase=False)
                    
                    meta = trz
                elif numberofcomp == 3:
                    continue
                else:
                    print('use vertical component or three components? try numberofcomp=1 or 3')

            tb = UTCDateTime(int(year),int(mon),int(day))
            te = tb + dayleng
            meta = meta.trim(tb, te, pad=True, fill_value=0)
            tb = meta[0].stats.starttime - origins
            filename = "%04d_%02d_%02d_%08.2f_%s_%s_mseed" % (int(year),int(mon),int(day),tb,net,sta)
            mseed = os.path.join(processed_waveform_dir,filename)
            meta.write(mseed, format="mseed")
            o.write('{}\n'.format(filename))
            p.write(station)
o.close()
f.close()
