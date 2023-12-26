#!/usr/bin/env python
# coding: utf-8

#obspy is included in phasenet
#type 'conda activate phasenet' first
# If you missed some data, try to run it again.

from obspy import UTCDateTime, read
from obspy.clients.fdsn import Client
from datetime import datetime, timedelta, timezone
import os

# Date and time 
year0 = 2016 # year
mon0 = 10 # month
day0 = 14 #day
nday = 1 # number of days
tb = 0 # beginning time
te = 3000 # ending time, less than 200 M/day, for quick test
          # parameters in the code may not be optimal
#te = 86400 # ending time, over 5 G/day

stationfile="station_all.dat" # stations in the region

source1="INGV" # data provider
source2="IRIS" # data provider
client1 = Client(source1)
client2 = Client(source2)

# Define the data directory
data_dir = os.getcwd()
waveform_dir = os.path.join(data_dir, "waveform_sac")

# Create new directory
if not os.path.exists(waveform_dir):
    os.mkdir(waveform_dir)

for i in range(nday):
    origins = UTCDateTime(year0,mon0,day0) + 86400*i
    newdate = origins.strftime("%Y/%m/%d")
    year,mon,day = newdate.split('/')
    print(year,mon,day)
    dirdata = os.path.join(waveform_dir,year+mon+day)

    if not os.path.exists(dirdata):
        os.makedirs(dirdata)

    # Start and end time of waveforms
    tbeg = origins + timedelta(seconds=tb)
    tend = origins + timedelta(seconds=te)

    with open(stationfile, "r") as f:
        for station in f:
            stlo, stla, net, sta, chan, elev = station.split()
            chane = chan[:2]+"E"
            chann = chan[:2]+"N"
            chanz = chan[:2]+"Z"
            chan0 = [chane,chann,chanz]
            for chan1 in chan0:
                print(net,sta,chan1)
                trace = os.path.join(dirdata,net+'.'+sta+'.'+chan1)
                if os.path.exists(trace):
                    print('downloaded already',net,sta,chan1)
                    continue

                try:
                    st = client1.get_waveforms(network=net,station=sta,channel=chan1,starttime=tbeg,endtime=tend,location=False,attach_response=True)
                    st.merge(method=1, fill_value='interpolate')
                    st.interpolate(sampling_rate=100,startime=tbeg)
                    st = st.trim(tbeg, tend, pad=True, fill_value=0)
                    st.detrend("demean")
                    st.detrend("linear")
                    pre_filt = [0.001, 0.002, 25, 30]
                    #response removal takes significant time
                    #If you don't remove response here, the magnitude output in REAL is meaningless
                    #If you decide to download raw data, you may remove response under the ../Magnitude directory to compute magnitude
                    st.remove_response(pre_filt=pre_filt,water_level=60,taper=True,taper_fraction=0.00001)
                    st[0].stats.sac = dict()
                    st[0].stats.sac.stla = stla
                    st[0].stats.sac.stlo = stlo
                    st[0].stats.sac.stel = elev
                    st[0].stats.sac.o = 0
                    st.write(filename=trace,format="SAC")
                except:
                    try:
                        st = client2.get_waveforms(network=net,station=sta,channel=chan1,starttime=tbeg,endtime=tend,location=False,attach_response=True)
                        st.merge(method=1, fill_value='interpolate')
                        st.interpolate(sampling_rate=100,startime=tbeg)
                        st = st.trim(tbeg, tend, pad=True, fill_value=0)
                        st.detrend("demean")
                        st.detrend("linear")
                        pre_filt = [0.001, 0.002, 25, 30]
                        st.remove_response(pre_filt=pre_filt,water_level=60,taper=True,taper_fraction=0.00001)
                        st[0].stats.sac = dict()
                        st[0].stats.sac.stla = stla
                        st[0].stats.sac.stlo = stlo
                        st[0].stats.sac.stel = elev
                        st[0].stats.sac.o = 0
                        st.write(filename=trace,format="SAC")
                    except:
                        print("doesn't exist",net,sta,chan1)
