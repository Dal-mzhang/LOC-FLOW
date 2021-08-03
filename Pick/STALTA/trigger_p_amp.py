import obspy
import os
import shutil
from obspy import read,UTCDateTime
from obspy.signal.trigger import recursive_sta_lta, trigger_onset, classic_sta_lta, plot_trigger
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

for d in range(nday):
    origins = UTCDateTime(year0,mon0,day0) + 86400*d
    newdate = origins.strftime("%Y/%m/%d")
    year,mon,day = newdate.split('/')

    print("Picking P phases: date %d / %d " % (d+1, nday))
    print(year,mon,day)

    date = str(year)+str(mon)+str(day)+'/'


    # Remove the old directory and create new one
    if os.path.isdir(date):
        shutil.rmtree(date)
    
    os.mkdir(date)

    with open(stationdir, "r") as f:
        for station in f:
            stlo, stla, net, sta, chan, elev = station.split()
            chanz = chan[:2]+"Z"
            chann = chan[:2]+"N"
            chane = chan[:2]+"E"
        
            wavez = ddir+date+net+'.'+sta+'.'+chanz
            wavee = ddir+date+net+'.'+sta+'.'+chane
            waven = ddir+date+net+'.'+sta+'.'+chann

            # try three components
            try:
                stz = read(wavez)
                ste = read(wavee)
                stn = read(waven)
                trz = stz[0]  
                tre = ste[0]
                trn = stn[0]

                trz.detrend('demean') 
                trz.detrend('linear') 
                trz.filter(type="bandpass",freqmin=2.0,freqmax=24.0,zerophase=False)
                df = trz.stats.sampling_rate
                tstart = trz.stats.starttime - UTCDateTime(int(year),int(mon),int(day)) 

                output = './'+date+net+'.'+sta+'.'+'P.txt'

                # Characteristic function and trigger onsets, see ObsPy website
                cft = recursive_sta_lta(trz.data, int(0.1 * df), int(2.5 * df))
                on_of = trigger_onset(cft, 6.0, 2.0)
                #plot_trigger(trz, cft, 6, 2)

                tre.simulate(paz_remove = None, paz_simulate = paz_wa, taper=True,taper_fraction=0.00001)
                trn.simulate(paz_remove = None, paz_simulate = paz_wa, taper=True,taper_fraction=0.00001)
                datatre = tre.data
                datatrn = trn.data

                # Output the triggered 
                f = open(output,'w')
                i = 0
                while(i<len(on_of)):
                    trig_on = on_of[i,0]
                    trig_of = on_of[i,1]
                    # consider 3 sec later to include potential S phase
                    trig_off = int(trig_of + (trig_of - trig_on)*4.0 + 3*df) 
                    if trig_off >= trz.stats.npts - 1:
                        break
                    # use a small triggering threshold to have more accurate picking time
                    # Read the largest amplitude in the follwing 4 times window of trig_of - trig_on
                    # 1000 is from meter to millimeter (mm) see Hutton and Boore (1987)
                    # use maximum amplitude (zero-to-peak)
                    # amp = max(max(abs(datatre[trig_on:trig_off])),max(abs(datatrn[trig_on:trig_off])))*1000
                    # use average amplitude (half peak-to-peak)
                    amp = (max(datatre[trig_on:trig_off])+abs(min(datatre[trig_on:trig_off]))+max(datatrn[trig_on:trig_off])+abs(min(datatrn[trig_on:trig_off])))/4*1000
                    if max(cft[trig_on:trig_of]) > 10.0:
                        f.write('%.4f %.4f %.4e\n' % ((tstart+trig_on/df),max(cft[trig_on:trig_of]),amp))
                    i=i+1
                f.close()
                #print('sation was used',net,sta)
            except:
                print('no station, skip the station',net,sta)
