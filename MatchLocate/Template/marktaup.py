import math
import obspy.taup
import numpy as ny
import glob
import os
import shutil
from obspy import read, UTCDateTime
from obspy.io.sac.util import obspy_to_sac_header
from obspy.taup import TauPyModel
from obspy.taup.taup_create import build_taup_model
from obspy.geodetics import locations2degrees

os.system('cp ../../REAL/tt_db/mymodel.nd .')
build_taup_model("mymodel.nd")
model = TauPyModel(model="mymodel")
os.remove('mymodel.nd')

catalog = '../catalog.dat' 
waveformdir = '../../Data/waveform_sac/'
INPUT = 'INPUT'
tleng = 100/2.5 # length of waveforms. e.g., (100 km) / (2.5 km/s)
bothps = 0 # use both P and S phases as templates, 0: only use S; 1: use both P and S
distmax = 0.2 # maximum distance in deg.

if os.path.exists(INPUT):
    shutil.rmtree(INPUT)
os.makedirs(INPUT)

with open(catalog, "r") as f:
    for event in f:
        date, time, lat, lon, dep, jk, mag = event.split()
        year,mon,day = date.split('/')
        hh,mm,sec = time.split(':')
        tb = UTCDateTime(int(year),int(mon),int(day),int(hh),int(mm),float(sec))
        te = tb + tleng
        st = read(os.path.join(waveformdir,year+mon+day+'/*.???'),starttime=tb,endtime=te)

        template = year+mon+day+hh+mm+sec
        if os.path.exists(template):
            shutil.rmtree(template)
        os.makedirs(template)
        
        if os.path.exists(os.path.join(INPUT,template)):
            shutil.rmtree(shutil.rmtree(INPUT,template))
        p = open(os.path.join(INPUT,template),"w")
        
        for tr in st:
            tr.stats.sac = obspy_to_sac_header(tr.stats)
            if tr.stats.channel[2] != 'Z' or tr.stats.sac.depmax == 0: # Too many traces, as example, just use Z comp. remove zero traces.
                continue
            tr.stats.starttime = tr.stats.starttime - tr.stats.sac.b
            stla = tr.stats.sac.stla
            stlo = tr.stats.sac.stlo
            tr.stats.sac.evla = lat
            tr.stats.sac.evlo = lon
            tr.stats.sac.evdp = dep
            tr.stats.sac.mag = mag
            tr.stats.sac.user0 = mag

            dist = locations2degrees(float(lat), float(lon), float(stla), float(stlo))
            arrivals = model.get_travel_times(source_depth_in_km=float(dep), distance_in_degree=dist, phase_list=["P","p","S","s"])
            i = 0
            pi = 0
            si = 0
            while(i<len(arrivals) and dist < distmax):
                arr = arrivals[i]
                i = i + 1
                if((arr.name == 'P' or arr.name == 'p') and pi == 0):
                    pname = arr.name
                    p_time = arr.time
                    p_ray_param = arr.ray_param*2*ny.pi/360
                    p_hslowness = -1*(p_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                    if bothps == 1:
                        p.write('%s %5.2f %.6e/%.6e 1 P\n' % (tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel,p_time,p_ray_param,p_hslowness))
                    tr.stats.sac.t1 = format(p_time,'.2f') # make sure it can be divided by your sampling rate (e.g., 0.01 sec)
                    pi = 1

                if((arr.name == 'S' or arr.name == 's') and si == 0):
                    sname = arr.name
                    s_time = arr.time
                    s_ray_param = arr.ray_param*2*ny.pi/360
                    s_hslowness = -1*(s_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                    p.write('%s %5.2f %.6e/%.6e 2 S\n' % (tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel,s_time,s_ray_param,s_hslowness))
                    tr.stats.sac.t2 = format(s_time,'.2f') # make sure it can be divided by your sampling rate (e.g., 0.01 sec)
                    si = 1
            
                if(pi == 1 and si == 1):
                    tr.write(os.path.join(template,tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel),format='SAC')
                    break

        p.close()
