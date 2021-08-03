#!/usr/bin/python -w
# verify events by checking all stations
# Here the P and S traveltimes are predicted by velocity model
# not our ouput picks
import glob
import os
from obspy import read,UTCDateTime, Stream
from matplotlib.transforms import blended_transform_factory
from obspy.geodetics import locations2degrees
import matplotlib.pyplot as plt
from obspy.geodetics import gps2dist_azimuth
import shutil
from obspy.io.sac.util import obspy_to_sac_header
from obspy.taup import TauPyModel
from obspy.taup.taup_create import build_taup_model

os.system('cp ../tt_db/mymodel.nd .')
build_taup_model("mymodel.nd")
model = TauPyModel(model="mymodel")

numID = 2359  # plot the waveforms with event ID
maxdt = 50/2.5 # maxdist/2.5 estimate the used length of waveform
tleng = maxdt # time window for waveform plotting
freqmin = 2 # low pass 
freqmax = 15 # high pass 
sacdir = '../../Data/waveform_sac' # sac file dir
phasefile= '../catalogSA_allday.txt' # phase list

iok = 0
with open(phasefile, "r") as f:
    for line in f:
        year, mon, day, hh, mm, sec, lat, lon, dep, mag, nofps, gap, res, num = line.split()
        if int(num) == numID:
            event = './'+year+mon+day+hh+mm+sec+'_'+nofps+'_'+gap+'_'+str(int(num))+'_all'
            if os.path.exists(event):
                shutil.rmtree(event)
            os.mkdir(event)
            
            station = sacdir+'/'+year+mon+day+'/'+'*.??Z'
            print(int(year),int(mon),int(day),float(hh),float(mm),float(sec))
            tb = UTCDateTime(int(year),int(mon),int(day),int(hh),int(mm),float(sec))
            te = tb + maxdt
            st = read(station,starttime=tb,endtime=te)
            st.trim(tb,te)
            for tr in st:
                tr.stats.sac = obspy_to_sac_header(tr.stats)
                tr.stats.sac.evla = lat
                tr.stats.sac.evlo = lon
                tr.stats.sac.evdp = dep
                tr.stats.sac.mag = mag
                stla = tr.stats.sac.stla
                stlo = tr.stats.sac.stlo
                tr.stats.starttime = tr.stats.starttime - tr.stats.sac.b
                tr.stats.sac.o = 0
                dist = locations2degrees(float(lat), float(lon), float(stla), float(stlo))
                arrivals = model.get_travel_times(source_depth_in_km=float(dep), distance_in_degree=dist, phase_list=["P","p","S","s"])
                i = 0
                pi = 0
                si = 0
                while(i<len(arrivals)):
                    arr = arrivals[i]
                    i = i + 1
                    if((arr.name == 'P' or arr.name == 'p') and pi == 0):
                        tr.stats.sac.t1 = arr.time
                        pi = 1

                    if((arr.name == 'S' or arr.name == 's') and si == 0):
                        s_time = arr.time
                        tr.stats.sac.t2 = arr.time
                        si = 1
                    if(pi == 1 and si == 1):
                        break
                tr.detrend()
                tr.taper(0.01,type='hann')
                tr.filter("bandpass", freqmin=freqmin, freqmax=freqmax)
                tr.write(os.path.join(event,tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel),format='SAC')
            break

os.remove('mymodel.nd')

with open(phasefile, "r") as f:
    for line in f:
        year, mon, day, hh, mm, sec, lat, lon, dep, mag, nofps, gap, res, num = line.split()
        if int(num) == numID:
            event = './'+year+mon+day+hh+mm+sec+'_'+nofps+'_'+gap+'_'+str(int(num))+'_all'
            waveform = event+'/*'
            st = read(waveform)

            for tr in st:
                tr.stats.distance = gps2dist_azimuth(tr.stats.sac.stla, tr.stats.sac.stlo,
                                        tr.stats.sac.evla, tr.stats.sac.evlo)[0]

            fig = plt.figure()
            st.plot(type='section', plot_dx=20e3, recordlength=tleng,
                time_down=False, linewidth=.25, grid_linewidth=.25, show=False, fig=fig)

            ax = fig.axes[0]
            transform = blended_transform_factory(ax.transData, ax.transAxes)
            for tr in st:
                ax.text(tr.stats.distance, 1, tr.stats.station, rotation=90,
                va="bottom", ha="center", transform=transform, zorder=10)
            plt.savefig(event+"/waveform.pdf")
            plt.show()
