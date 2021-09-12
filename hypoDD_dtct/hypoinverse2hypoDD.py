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
                    hour1 = int(line[25:27])
                    min1 = int(line[27:29])

                    if year1 == year and mon1 == mon and day1 == day and hour1 == hour and min1 == min:
                        sec_p =sec
                        if line[13:15] == ' P' or line[13:15] == 'IP':
                            P_residual = abs(int(line[34:38]) / 100)
                            sec_p = int(line[29:34]) / 100
                            if sec_p > sec and P_residual <= nres*RMS:
                                ppick = sec_p-sec
                                g.write('{:<5s}    {:8.3f}   1.000   P\n'.format(station, ppick))

                        if line[46:48] == ' S' or line[46:48] == 'ES':
                            S_residual = abs(int(line[50:54]) / 100)
                            sec_s = int(line[41:46]) / 100
                            if sec_s > sec_p and S_residual <= nres * RMS:
                                spick = sec_s-sec
                                g.write('{:<5s}    {:8.3f}   1.000   S\n'.format(station, spick))
    f.close()
    g.close()

if __name__ == '__main__':
    if len(sys.argv) != 9:
        print('hypoinverse2hypoDD.py hypoOut.arc hypoDD.pha rms_threshold gap_threshold pick_rms maxdep maxdeperr maxdiserr')
        sys.exit()
    format_convert(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7],sys.argv[8])
