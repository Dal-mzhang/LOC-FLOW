#!/usr/bin/python -w
# verify events with picks 
import glob
import os
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory
from obspy import read,UTCDateTime, Stream
from obspy.geodetics import gps2dist_azimuth
import shutil
from obspy.io.sac.util import obspy_to_sac_header


numID = 99 # use numID to check waveforms
#minnofps = 20 # verify events with specific number of picks 
#maxnofps = 20 # verify events with specific number of picks
maxdt = 50/2.5 # maxdist/2.5 estimate the used length of waveform
freqmin = 2 # low pass 
freqmax = 15 # high pass 
tleng = maxdt # time window for waveform plotting
sacdir = '../../Data/waveform_sac' # sac file dir
phasefile= './phase_sel_all.txt' # phase list

os.system("cat ../*.phase_sel.txt > phase_sel_all.txt")

with open(phasefile, "r") as f:
    for line in f:
        if (len(line) > 100):
            num, year, mon, day, time, orgt, res, lat, lon, dep, mag, magdev, nofp, nofs, nofps, pofbothps, gap = line.split()
            iok = 0
            #if int(nofps) <= maxnofps and int(nofps) >= minnofps:
            if int(num) == numID:
                print(year+mon+day,time,nofps,gap)
                hh, mm, sec = time.split(':')
                event = './'+year+mon+day+hh+mm+sec+'_'+nofps+'_'+gap+'_'+num+'_pick'
                print(event)
                if os.path.exists(event):
                    shutil.rmtree(event)
                os.mkdir(event)
                iok = 1
        else:
            if (iok == 1 and len(line) < 100):
                #print(line)
                net, sta, phase, tabs, trelative, amp, tres, tweig, tbaz = line.split()
                station1 = sacdir+'/'+year+mon+day+'/'+net+'.'+sta+'.'+'???'
                station2 = event+'/'+net+'.'+sta+'.'+'???'
                st = read(station1)
                sacfile = event+'/'+st[0].stats.network+'.'+st[0].stats.station+'.'+st[0].stats.channel
                if not os.path.isfile(sacfile):
                    for tr in st:
                        tb = UTCDateTime(int(year),int(mon),int(day))+float(orgt)
                        te = tb + maxdt
                        tr.trim(tb,te)
                        tr.stats.sac = obspy_to_sac_header(tr.stats)
                        tr.stats.sac.evla = lat
                        tr.stats.sac.evlo = lon
                        tr.stats.sac.evdp = dep
                        tr.stats.sac.mag = mag
                        tr.stats.starttime = tr.stats.starttime - tr.stats.sac.b
                        tr.stats.sac.o = 0
                        if phase == 'P':
                            tr.stats.sac.t1 = trelative
                        else:
                            tr.stats.sac.t2 = trelative
                        tr.detrend()
                        tr.taper(0.01,type='hann')
                        tr.filter("bandpass", freqmin=freqmin, freqmax=freqmax)
                        tr.write(os.path.join(event,tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel),format='SAC')
                else:
                    st = read(station2)
                    for tr in st:
                        tr.stats.sac = obspy_to_sac_header(tr.stats)
                        if phase == 'P':
                            tr.stats.sac.t1 = trelative
                        else:
                            tr.stats.sac.t2 = trelative
                        tr.write(os.path.join(event,tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.channel),format='SAC')
            else:
                continue

with open(phasefile, "r") as f:
    for line in f:
        if (len(line) > 100):
            num, year, mon, day, time, orgt, res, lat, lon, dep, mag, magdev, nofp, nofs, nofps, pofbothps, gap = line.split()
            iok = 0 
            #if int(nofps) <= maxnofps and int(nofps) >= minnofps:
            if (int(num) == numID):
                hh, mm, sec = time.split(':')
                event = './'+year+mon+day+hh+mm+sec+'_'+nofps+'_'+gap+'_'+num+'_pick'
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

os.remove(phasefile)
