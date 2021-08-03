import obspy
import os
from obspy import read,UTCDateTime
from obspy.signal.trigger import recursive_sta_lta, trigger_onset, classic_sta_lta
import warnings
import numpy as np
from obspy import UTCDateTime
# how to pick phases using STA/LTA method? Please refer to
# https://docs.obspy.org/tutorial/code_snippets/trigger_tutorial.html

ddir = '../../Data/waveform_sac/'
stationdir = '../../Data/station.dat'

year0 = 2016 # year
mon0 = 10 # mon
day0 = 14 # day
nday = 1 # number of days

# https://docs.obspy.org/_modules/obspy/signal/invsim.html
paz_wa = {'poles': [-6.283 + 4.7124j, -6.283 - 4.7124j],
                'zeros': [0 + 0j], 'gain': 1.0, 'sensitivity': 2080}

def main():
    for d in range(nday):
        origins = UTCDateTime(year0,mon0,day0) + 86400*d
        newdate = origins.strftime("%Y/%m/%d")
        year,mon,day = newdate.split('/')

        print("Picking S phases: date %d / %d " % (d+1, nday))
        print(year,mon,day)

        date = str(year)+str(mon)+str(day)+'/'

        if not os.path.exists(date):
            os.makedirs(date)

        with open(stationdir, "r") as f:
            for station in f:
                stlo, stla, net, sta, chan, elev = station.split()
                chane = chan[:2]+"E"
                chann = chan[:2]+"N"

                wave_e = ddir+date+net+'.'+sta+'.'+chane
                wave_n = ddir+date+net+'.'+sta+'.'+chann
                try:
                    ste = read(wave_e)
                    stn = read(wave_n)
                    
                    ste.detrend('demean') 
                    ste.detrend('linear') 
                    stn.detrend('demean') 
                    stn.detrend('linear') 
                    ste.filter(type="bandpass",freqmin=2.0,freqmax=15.0,zerophase=False)
                    stn.filter(type="bandpass",freqmin=2.0,freqmax=15.0,zerophase=False)
                    
                    tre = ste[0]
                    trn = stn[0]
                    
                    df = tre.stats.sampling_rate
                    tstart = tre.stats.starttime - UTCDateTime(int(year), int(mon), int(day))
                    
                    output = './'+date+net+'.'+sta+'.'+'S.txt'
                    if os.path.isfile(output):
                        os.remove(output)

                    # Characteristic function and trigger onsets
                    cft = recSTALTAPy_h(tre.data, trn.data, int(0.2 * df), int(2.5 * df))
                    on_of = trigger_onset(cft, 4.0, 2.0)
                    
                    wa_e = read(wave_e)
                    wa_n = read(wave_n)
                    wa_e.simulate(paz_remove = None, paz_simulate = paz_wa, taper=True,taper_fraction=0.00001)
                    wa_n.simulate(paz_remove = None, paz_simulate = paz_wa, taper=True,taper_fraction=0.00001)
                    datatre = wa_e[0].data
                    datatrn = wa_n[0].data

                    # Output the triggered 
                    f = open(output,'w')
                    i = 0
                    while(i<len(on_of)):
                        trig_on = on_of[i,0]
                        trig_of = on_of[i,1]
                        trig_off = int(trig_of + (trig_of - trig_on)*4.0)
                        if trig_off >= tre.stats.npts - 1:
                            break
                        # use a small triggering threshold to have more accurate picking time
                        # Read the largest amplitude in the follwing 4 times window of trig_of - trig_on
                        # 1000 is from meter to millimeter (mm) see Hutton and Boore (1987)
                        # use maximum amplitude (zero-to-peak)
                        # amp = max(max(abs(datatre[trig_on:trig_off])),max(abs(datatrn[trig_on:trig_off])))*1000
                        # use average amplitude (half peak-to-peak)
                        amp = (max(datatre[trig_on:trig_off])+abs(min(datatre[trig_on:trig_off]))+max(datatrn[trig_on:trig_off])+abs(min(datatrn[trig_on:trig_off])))/4*1000

                        if max(cft[trig_on:trig_of]) > 6.0:
                            f.write('{} {} {}\n'.format(tstart+trig_on/df,max(cft[trig_on:trig_of]),amp))
                        i=i+1
                    f.close()
                except:
                    print('no station, skip the station',net,sta)


def recSTALTAPy_h(a, b, nsta, nlta):
    """
    Recursive STA/LTA written in Python.

    .. note::

        There exists a faster version of this trigger wrapped in C
        called :func:`~obspy.signal.trigger.recSTALTA` in this module!

    :type a: NumPy ndarray
    :param a: Seismic Trace
    :type nsta: Int
    :param nsta: Length of short time average window in samples
    :type nlta: Int
    :param nlta: Length of long time average window in samples
    :rtype: NumPy ndarray
    :return: Characteristic function of recursive STA/LTA

    .. seealso:: [Withers1998]_ (p. 98) and [Trnkoczy2012]_
    """
    try:
        a = a.tolist()
    except:
        pass

    try:
        b = b.tolist()
    except:
        pass
    ndat = len(a)
    # compute the short time average (STA) and long time average (LTA)
    csta = 1. / nsta
    clta = 1. / nlta
    sta = 0.
    lta = 1e-99  # avoid zero devision
    charfct = [0.0] * len(a)
    icsta = 1 - csta
    iclta = 1 - clta
    for i in range(1, ndat):
        sq = a[i] ** 2 + b[i] ** 2
        sta = csta * sq + icsta * sta
        lta = clta * sq + iclta * lta
        charfct[i] = sta / lta
        if i < nlta:
            charfct[i] = 0.
    return np.array(charfct)

if __name__ == '__main__':
    main()
