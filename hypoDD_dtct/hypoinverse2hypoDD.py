#!/usr/bin/python -w
import datetime
import math
import sys

def format_convert(phaseinput,phaseoutput,nrms,ngap,nres,maxdep,maxdeperr,maxdiserr):
#phaseinput = 'hypoOut.arc' # phase file output by hypoinverse
#phaseoutput = 'hypoDD.pha' # input phase file for hypoDD

    g = open(phaseoutput, 'w')
    #nn = 100000
    nn = 0
    nres = float(nres)
    nrms = float(nrms)
    ngap = int(ngap)
    maxdep = float(maxdep)
    maxdeperr = float(maxdeperr)
    maxdiserr = float(maxdiserr)

    with open(phaseinput, "r") as f:
        for line in f:
            if (len(line) == 180):
                iok = 0
                RMS = float(line[48:52]) / 100
                gap = int(line[42:45])
                dep = float(line[31:36])/100
                EZ = float(line[89:93])/100
                EH = float(line[85:89])/100

                if RMS <= nrms and gap <= ngap and dep <= maxdep and EZ <= maxdeperr and EH <= maxdiserr:
                    nn = nn + 1
                    year = int(line[0:4])
                    mon = int(line[4:6])
                    day = int(line[6:8])
                    hour = int(line[8:10])
                    min = int(line[10:12])
                    sec = int(line[12:16])/100
                    d0 = datetime.datetime(year, mon, day, hour, min, int(math.modf(sec)[1]), int((math.modf(sec)[0]) * 1000000))

                    if line[18] == ' ': #N
                        lat = (float(line[16:18]) + float(line[19:23]) / 6000)
                    else:
                        lat = float(line[16:18]) + float(line[19:23])/6000 * (-1)

                    if line[26] == 'E':
                        lon = (float(line[23:26]) + float(line[27:31]) / 6000)
                    else:
                        lon = (float(line[23:26]) + float(line[27:31]) / 6000) * (-1)

                    mag = float(line[123:126])/100
                    g.write(
                        '# {:4d} {:2d} {:2d} {:2d} {:2d} {:5.2f}  {:7.4f} {:9.4f}   {:5.2f} {:5.2f} {:5.2f} {:5.2f} {:5.2f} {:9d}\n'.format(
                            year, mon, day, hour, min, sec, lat, lon, dep, mag, EH, EZ, RMS, nn))
                    iok = 1
            else:
                if (iok == 1 and len(line) == 121):
                    station = line[0:5]
                    net = line[5:7]
                    year1 = int(line[17:21])
                    mon1 = int(line[21:23])
                    day1 = int(line[23:25])
                    if line[13:15] == ' P' or line[13:15] == 'IP':
                        hour1 = int(line[25:27])
                        min1 = int(line[27:29])
                        P_residual = abs(int(line[34:38]) / 100)
                        sec1 = int(line[29:34]) / 100
                        if sec1 >= 60:
                            min1 = min1 + int(sec1//60)
                            sec1 = sec1%60
                        if min1 >= 60:
                            hour1 = hour1 + int(min1 // 60)
                            min1 = min1 % 60

                        d1 = datetime.datetime(year1, mon1, day1, hour1, min1, int(math.modf(sec1)[1]), int((math.modf(sec1)[0]) * 1000000))
                        if sec1 > sec and P_residual <= nres*RMS:
                            tpick = (d1-d0).seconds + ((d1-d0).microseconds)/1000000
                            g.write('{:<5s}    {:8.3f}   1.000   P\n'.format(station, tpick))

                    if line[46:48] == ' S' or line[46:48] == 'ES':
                        hour1 = int(line[25:27])
                        min1 = int(line[27:29])
                        S_residual = abs(int(line[50:54]) / 100)
                        sec2 = int(line[41:46]) / 100
                        if sec2 >= 60:
                            min1 = min1 + int(sec2 // 60)
                            sec2 = sec2 % 60
                        if min1 >= 60:
                            hour1 = hour1 + int(min1 // 60)
                            min1 = min1 % 60
                        d2 = datetime.datetime(year1, mon1, day1, hour1, min1, int(math.modf(sec2)[1]), int((math.modf(sec2)[0]) * 1000000))
                        if sec2 > sec1 and S_residual <= nres * RMS:
                            tpick = (d2 - d0).seconds + ((d2 - d0).microseconds) / 1000000
                            g.write('{:<5s}    {:8.3f}   1.000   S\n'.format(station, tpick))
    f.close()
    g.close()

if __name__ == '__main__':
    if len(sys.argv) != 9:
        print('hypoinverse2hypoDD.py hypoOut.arc hypoDD.pha rms_threshold gap_threshold pick_rms maxdep maxdeperr maxdiserr')
        sys.exit()
    format_convert(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7],sys.argv[8])
