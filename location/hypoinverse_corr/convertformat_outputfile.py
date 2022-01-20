#!/usr/bin/python -w
import datetime
import math
import sys

def format_convert(inputfile,outputfile,deletefile,nEH,nEZ,ngap,nrms):
#inputfile = 'hypoOut.arc' # phase file output by hyp1.40
#outputfile = 'new.cat'
#deletefile = 'dele.cat'

    g = open(outputfile, 'w')
    k = open(deletefile, 'w')
    nn = 0
    nEH = float(nEH)
    nEZ = float(nEZ)
    ngap = int(ngap)
    nrms = float(nrms)

    with open(inputfile, "r") as f:
        for line in f:
            if (len(line) == 180):
                nn = nn + 1
                RMS = float(line[48:52]) / 100
                gap = int(line[42:45])
                dep = float(line[31:36])/100
                EH = float(line[85:89])/100
                EZ = float(line[89:93])/100
                mag = float(line[123:126])/100
                    
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


                if RMS <= nrms and gap <= ngap and EH <= nEH and EZ <= nEZ:
                    g.write(
                        '{:4d}{:02d}{:02d} {:2d} {:2d} {:5.2f} {:7.4f} {:9.4f}  {:5.2f} {:5.2f} {:5.2f} {:5.2f} {:5.2f} {:9d}\n'.format(
                            year, mon, day, hour, min, sec, lat, lon, dep, mag, RMS, EH, EZ, nn))
                else:
                    k.write(
                        '{:4d}{:02d}{:02d} {:2d} {:2d} {:5.2f} {:7.4f} {:9.4f}  {:5.2f} {:5.2f} {:5.2f} {:5.2f} {:5.2f} {:9d}\n'.format(
                            year, mon, day, hour, min, sec, lat, lon, dep, mag, RMS, EH, EZ, nn))
    f.close()
    g.close()
    k.close()

if __name__ == '__main__':
    if len(sys.argv) != 8:
        print('convertformat_outputfile.py hypoOut.arc new.cat dele.cat nEH nEZ ngap nrms')
        sys.exit()
    format_convert(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7])
