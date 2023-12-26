#!/usr/bin/env python
# coding: utf-8

#obspy is included in phasenet
#type 'conda activate phasenet' first

# Import modules
import math
import numpy as np
import pandas as pd
import os
import shutil
from time import time
from datetime import datetime, timedelta, timezone
from obspy import UTCDateTime, read, read_inventory, read_events
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.mass_downloader import (
    CircularDomain,
    Restrictions,
    MassDownloader,
)

# Date and time 
year0 = 2016 # year
mon0 = 10 # month
day0 = 14 #day
nday = 1 # number of days
tb = 0 # beginning time
te = 3000 # ending time, for quick test
#te = 86400 # ending time, the whole day
samplingrate = 100 # resampling rate in Hz

# Station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
network= "IV,YR" # network
channels = ["HH?","EH?"] # station channel priority, 
# If not specified, default channel_priorities: 
#"HH[ZNE12]", "BH[ZNE12]","MH[ZNE12]", "EH[ZNE12]", "LH[ZNE12]", "HL[ZNE12]"
#"BL[ZNE12]", "ML[ZNE12]", "EL[ZNE12]", "LL[ZNE12]", "SH[ZNE12]"),
#https://ds.iris.edu/ds/nodes/dmc/data/formats/seed-channel-naming/

# Define the data directories
data_dir = os.getcwd()
raw_waveform_dir = os.path.join(data_dir, "waveform_mseed")
processed_waveform_dir = os.path.join(data_dir, "waveform_sac")

fname = 'station_all.dat'
o = open(fname,"w")

# Remove the old directories and create new ones
if os.path.isdir(raw_waveform_dir):
    shutil.rmtree(raw_waveform_dir)
os.mkdir(raw_waveform_dir)

if os.path.isdir(processed_waveform_dir):
    shutil.rmtree(processed_waveform_dir)
os.mkdir(processed_waveform_dir)

# Write station information into sac header
def obspy_to_sac_header(stream, inventory):
    for tr in stream:

        # Add stats for SAC format
        tr.stats.sac = dict()

        # Add station and channel information
        metadata = inventory.get_channel_metadata(tr.id)
        tr.stats.sac.stla = metadata["latitude"]
        tr.stats.sac.stlo = metadata["longitude"]
        tr.stats.sac.stel = metadata["elevation"]
        tr.stats.sac.stdp = metadata["local_depth"]
        tr.stats.sac.cmpaz = metadata["azimuth"]
        tr.stats.sac.cmpinc = metadata["dip"] + 90 # different definitions
        
        # set event origin time as reference time
        tr.stats.sac.o = 0

t0 = time()
ETA = 0
k = -1

for i in range(nday):
    # Calculate ETA based on average processing time
    running_time = time() - t0
    days_per_sec = (i + 1) / running_time
    days_to_do = nday - i
    ETA = days_to_do / days_per_sec
    
    origins = UTCDateTime(year0,mon0,day0) + 86400*i
    newdate = origins.strftime("%Y/%m/%d")
    year,mon,day = newdate.split('/')
    
    print("Fetching date %d / %d [ETA: %.d s]" % (i+1, nday, ETA))
    print(year,mon,day)
    k += 1

    # Start and end time of waveforms
    starttime= origins + timedelta(seconds=tb)
    endtime = origins + timedelta(seconds=te)
    
    domain = CircularDomain(
        latitude=latref, longitude=lonref, minradius=0.0, maxradius=maxradius/111.19
    )
    
    # see https://docs.obspy.org/packages/autogen/obspy.clients.fdsn.mass_downloader.html
    restrictions = Restrictions(
        starttime=starttime,
        endtime=endtime,
        reject_channels_with_gaps=False,
        #channel="", # use all available channels if not provided
        channel_priorities=channels,
        network=network, # use all available networks if not provided
        #station="",
        #location="00",
        minimum_length = 0.5,
        sanitize=False,
    )

    eventid_dir = os.path.join(raw_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))
    if os.path.isdir(eventid_dir):
        shutil.rmtree(eventid_dir)
    os.mkdir(eventid_dir)

    # use all available providers
    mdl = MassDownloader() 

    # Get the data (if available) and write to output file
    mdl.download(domain, restrictions, mseed_storage=eventid_dir, stationxml_storage=eventid_dir)
    # Remove the response, write header, rotate components
    st = read(os.path.join(eventid_dir,"*.mseed"))
    inv = read_inventory(os.path.join(eventid_dir,"*.xml"))
    st.merge(method=1, fill_value='interpolate')
    st = st.trim(starttime, endtime, pad=True, fill_value=0)
    for tr in st: 
        if np.isnan(np.max(tr.data)) or np.isinf(np.max(tr.data)):
            st.remove(tr)
    st.detrend("demean")
    st.detrend("linear")
    st.interpolate(sampling_rate=samplingrate,startime=tb)
    #response removal takes significant time
    #If you don't remove response here, the magnitude output in REAL is meaningless
    #If you decide to download raw data, you may remove response under the ../Magnitude directory to compute magnitude
    pre_filt = [0.001, 0.002, 25, 30]
    st.attach_response(inv)
    st.remove_response(pre_filt=pre_filt,water_level=60,taper=True,taper_fraction=0.00001)
    obspy_to_sac_header(st, inv)
    st.rotate(method="->ZNE", inventory=inv) #rotate to ZNE, optional, recommended, FDTCC only recognizes ENZ
    sacid_dir = os.path.join(processed_waveform_dir,"%04d%02d%02d" % (int(year),int(mon),int(day)))

    if os.path.isdir(sacid_dir):
        shutil.rmtree(sacid_dir)
    os.mkdir(sacid_dir)

    for tr in st:
        traceid=os.path.join(sacid_dir,tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel)
        if tr.stats.channel[2] == 'Z':
            o.write('{} {} {} {} {} {}\n'.format(tr.stats.sac.stlo,tr.stats.sac.stla,tr.stats.network,tr.stats.station,tr.stats.channel,tr.stats.sac.stel/1000))
        tr.write(traceid, format="SAC")
    
    print("Data on %04d-%02d-%02d found" % (int(year),int(mon),int(day)))
    shutil.rmtree(eventid_dir)
o.close()

shutil.rmtree(raw_waveform_dir)
os.system ("cat {} | sort -u -k 4 | uniq > uniq_st.dat && mv uniq_st.dat {}".format (fname, fname)) # remove duplicated stations
