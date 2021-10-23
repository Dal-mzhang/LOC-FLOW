# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 22:04:17 2019

@author: Jiupeng
"""
#Modified from Jiupeng Hu

#from __future__ import print_function
from collections import defaultdict
import os
import sys
import datetime

def decdeg2dms(dd):
    deg, mnt = divmod(dd*60.0, 60)
    return int(deg), mnt
def gen_sta_hypo(stationin):
    output = 'station.dat'
    g = open(output,'w')
    with open(stationin, 'r') as fr:
        for line in fr.readlines():
            line = line.strip().split()
            lat_0=float(line[1])
            lon_0=float(line[0])
            latD, latM = decdeg2dms(abs(lat_0))
            lonD, lonM = decdeg2dms(abs(lon_0))
            if lat_0 > 0 and lon_0 >= 0:
                for channel in ['001', '002', '003']:
                    #g.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f} {:3d} {:7.4f}E{:4d}\n'.format(line[3], line[2], channel ,latD, latM, lonD, lonM, 0))
                    g.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f}N{:3d} {:7.4f}E{:4d}\n'.format(line[3], line[2], channel ,latD, latM, lonD, lonM, int(float(line[5])*1000)))
            if lat_0 > 0 and lon_0 < 0:
                for channel in ['001', '002', '003']:
                    g.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f}N{:3d} {:7.4f}W{:4d}\n'.format(line[3], line[2], channel ,latD, latM, lonD, lonM, int(float(line[5])*1000)))
            if lat_0 <= 0 and lon_0 >= 0:
                for channel in ['001', '002', '003']:
                    g.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f}S{:3d} {:7.4f}E{:4d}\n'.format(line[3], line[2], channel ,latD, latM, lonD, lonM, int(float(line[5])*1000)))
            if lat_0 <= 0 and lon_0 < 0:
                for channel in ['001', '002', '003']:
                    g.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f}S{:3d} {:7.4f}W{:4d}\n'.format(line[3], line[2], channel ,latD, latM, lonD, lonM, int(float(line[5])*1000)))


class Event(object):
    def __init__(self,line):
        eventParts = line.split()
        # assert len(eventParts) == 10
        self.no = eventParts[0]
        self.year = eventParts[1]
        self.month = eventParts[2]
        self.day = eventParts[3]
        self.stime = eventParts[4] # time string
        self.dtime = eventParts[5] # time delta to 00:00
        self.std = eventParts[6]
        self.lat = eventParts[7]
        self.lon = eventParts[8]
        self.depth = eventParts[9]
        self.mag = eventParts[10]
        self.stations = set([])

    def setSta(self, sta):
        self.sta = sta

    def setPicks(self, stationPicks):
        self.stationPicks = stationPicks

    def __repr__(self):
        return ' '.join([self.year, self.month, self.day, self.stime, self.lat+self.lon])


class Pick(object):
    def __init__(self, line):
        phaseParts = line.split()
        self.net = phaseParts[0]
        self.staN = phaseParts[1]
        self.sta = '.'.join([self.net, self.staN])
        self.phase = phaseParts[2]
        self.dtime = phaseParts[3] # time to 00:00
        self.ttime = phaseParts[4] # travel time
        self.pamp = phaseParts[5] # P phase amplitude
        self.error = phaseParts[6] # travel time errors from taup_time

    def __str__(self):
        return self.net+self.sta+self.dtime
    def __repr__(self):
        return ' '.join([self.net, self.sta,self.phase,self.ttime, self.dtime, self.pamp, self.error])


def isEqLine(line):
    if line[19] in ['P','S']:
        return False
    else:
        return True

class SeismicReport(object):
    def __init__(self, eventsFile):
        self.events = []
        self.readEventsFile(eventsFile)

    def readEventsFile(self, eventsFile):
        eventNo = 0
        stationPicks = []
        with open(eventsFile, 'r') as f:
            line = f.readline()
            # Process first line particularly
            while line:
                # if line[0].isspace(): # Event line start with spaces
                if isEqLine(line):
                    pickNo = 0
                    eventNo += 1
                    eventTemp = Event(line)
                    line = f.readline()
                    break
                else:
                    line = f.readline()
            while line:
                # if line[0].isspace():
                if isEqLine(line):
                    if stationPicks:
                        eventTemp.setPicks(stationPicks)
                        self.events.append(eventTemp)
                    pickNo   = 0
                    eventNo += 1
                    stationPicks = []
                    eventTemp = Event(line)
                # elif line.startswith(stationPrompt):
                # elif line[0].isalpha():
                elif not isEqLine(line):
                    pickNo += 1
                    pickTemp = Pick(line)
                    eventTemp.stations.add(pickTemp.sta)
                    stationPicks.append(pickTemp)
                else:
                    print('Error!')
                line = f.readline()
            eventTemp.setPicks(stationPicks)
            self.events.append(eventTemp)

    def makeCatlog(self, phases=['P', 'Pg']):
        for event in self.events:
            for pick in event.stationPicks:
                if pick.phase.strip() in phases:
                    self.show([pick.net, pick.sta, pick.phase, event.year, event.month, event.day,
                               pick.dtime, event.lon, event.lat, event.depth])
            print("Eq: ",event.no)

    def makeHypoPhase(self):
        # Event format from "Summary header format Y2000"
        eventFormat1="{:4s}{:2s}{:2s}{:02d}{:02d}{:02d}{:02d}{:02d} {:>2d}{:02d}{:>3d}E{:>2d}{:02d}{:>3d}{:02d}                                                                                      {:1s}{:>1d}{:02d}"
        eventFormat2="{:4s}{:2s}{:2s}{:02d}{:02d}{:02d}{:02d}{:02d} {:>2d}{:02d}{:>3d} {:>2d}{:02d}{:>3d}{:02d}                                                                                      {:1s}{:>1d}{:02d}"
        eventFormat3="{:4s}{:2s}{:2s}{:02d}{:02d}{:02d}{:02d}{:02d}S{:>2d}{:02d}{:>3d}E{:>2d}{:02d}{:>3d}{:02d}                                                                                      {:1s}{:>1d}{:02d}"
        eventFormat4="{:4s}{:2s}{:2s}{:02d}{:02d}{:02d}{:02d}{:02d}S{:>2d}{:02d}{:>3d} {:>2d}{:02d}{:>3d}{:02d}                                                                                      {:1s}{:>1d}{:02d}"
        for event in self.events:
            # if len(event.stations) < 15:
            #     continue
            hour, minute, second = event.stime.split(':')
            if(int(hour) < 0 or int(minute) < 0 or float(second) < 0): 
                continue
            mag1,mag2 = event.mag.split('.')
            mag1 = int(mag1)
            mag2 = int(mag2[0:2])
            if float(event.mag) < 0:
                mag1 = 0
                mag2 = 0
            sec1 = second[0:2]
            sec2 = second[3:5]
            lat1, lat2, lat3 = self.processLatLon(event.lat)
            lon1, lon2, lon3 = self.processLatLon(event.lon)
            dep1, dep2 = self.processDep(event.depth)
            # print("0123456789012345678901234567890123456789012345678901234567890")
            if lat1 > 0 and lon1 >= 0:
                print(eventFormat1.format(event.year,event.month,event.day,int(hour),int(minute),int(sec1),int(sec2),lat1,lat2,lat3,lon1,lon2,lon3,dep1,dep2,'L',mag1,mag2))
            if lat1 > 0 and lon1 < 0:
                lon1=(-1)*lon1
                print(eventFormat2.format(event.year,event.month,event.day,int(hour),int(minute),int(sec1),int(sec2),lat1,lat2,lat3,lon1,lon2,lon3,dep1,dep2,'L',mag1,mag2))
            if lat1 <= 0 and lon1 >= 0:
                lat1=(-1)*lat1
                print(eventFormat3.format(event.year,event.month,event.day,int(hour),int(minute),int(sec1),int(sec2),lat1,lat2,lat3,lon1,lon2,lon3,dep1,dep2,'L',mag1,mag2))
            if lat1 <= 0 and lon1 < 0:
                lat1=(-1)*lat1
                lon1=(-1)*lon1
                print(eventFormat4.format(event.year,event.month,event.day,int(hour),int(minute),int(sec1),int(sec2),lat1,lat2,lat3,lon1,lon2,lon3,dep1,dep2,'L',mag1,mag2))
            #print(eventFormat.format(event.year,event.month,event.day,int(hour),int(minute),int(sec1),int(sec2),lat1,lat2,lat3,*lon1,lon2,lon3,dep1,dep2,'L',mag1,mag2))
            otimeStr = event.year+event.month+event.day+" "+event.stime
            otime = datetime.datetime.strptime(otimeStr, '%Y%m%d %H:%M:%S.%f')
            baseTime = otime - datetime.timedelta(seconds=otime.second, microseconds=otime.microsecond)

            tmpPicks = event.stationPicks.copy()
            for sta in event.stations:
                p_flag = False
                p_label = ' '
                s_flag = False
                s_lable = ' '
                sta_code = "001"
                tRes = '    '
                pWeight = '   '
                pSec = ''
                sSec =''
                sec1 = ''
                sec2 = ''

                for pick in tmpPicks[::-1]:
                    if pick.sta == sta:
                        if pick.phase == 'P':
                            p_travel_time = pick.ttime
                            p_flag = True
                        if pick.phase == 'S':
                            s_travel_time = pick.ttime
                            s_flag = True
                        if p_flag:
                            ptime = otime + datetime.timedelta(seconds=float(p_travel_time))
                            pDelta = ptime - baseTime
                            p_label = 'P'
                            # if(int(pDelta.seconds) > 100):
                            #     print('Error')
                            pSec = f'{pDelta.seconds:0>2}'
                            sec1 = f'{int(pDelta.microseconds/10000):0>2}'
                        if s_flag:
                            stime = otime + datetime.timedelta(seconds=float(s_travel_time))
                            sDelta = stime - baseTime
                            s_lable = 'S'
                            # if(int(sDelta.seconds) > 100):
                            #     print('Error')
                            sSec = f'{sDelta.seconds:0>2}'
                            sec2 = f'{int(sDelta.microseconds/10000):0>2}'

                phaseFormat="{:<5s}{:2s}  {:3s}  {:1s}  {:4d}{:02d}{:02d}{:02d}{:02d}{:>3s}{:2s}{:4s}{:3s}{:>3s}{:2s} {:1s}"


                print(phaseFormat.format(
                    sta.split('.')[1], sta.split('.')[0], sta_code, p_label,
                    baseTime.year, baseTime.month,baseTime.day,baseTime.hour,baseTime.minute,
                    pSec, sec1, tRes, pWeight, sSec, sec2, s_lable
                ))
            print('')
        # print("0123456789012345678901234567890123456789012345678901234567890")

    def processLatLon(self, value:float):
        value1, tmp = divmod(float(value)*60.0, 60)
        try:
            value2 = str(tmp).split('.')[0]
        except:
            value2 = 0
        try:
            value3 = str(tmp).split('.')[1][0:2]
            if len(value3) == 1:
                value3 = int(value3)*10
        except:
            value3 = 0
        return int(value1), int(value2), int(value3)

    def processDep(self, depth):
        try:
            dep1 = str(depth).split('.')[0]
        except:
            dep1 = 0
        try:
            dep2 = str(depth).split('.')[1][0:2]
            if len(dep2) == 1:
                dep2 = int(dep2)*10
        except:
            dep2 = 0
        return int(dep1), int(dep2)


    def show(self, list):
        outStr = ''
        for item in list:
            outStr = outStr + item + ' '
        print(outStr)

        
if __name__ == '__main__':
    # test = SeismicReport('phase_sel_one')
    if len(sys.argv) != 3:
        print('mk_input.py phasefile stationfile')
        sys.exit()
    gen_sta_hypo(sys.argv[2])
    test = SeismicReport(sys.argv[1])
    #test.makeCatlog()
    test.makeHypoPhase()
