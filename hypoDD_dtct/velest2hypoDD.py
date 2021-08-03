#!/usr/bin/python -w
import sys

def format_convert(phaseinput,phaseoutput,nrms,ngap,maxdep):
#phaseinput = 'final.CNV' # phase file output by hypoinverse
#phaseoutput = 'hypoDD.pha' # input phase file for hypoDD
    year0 = '20'
    #year0 = '19' 
    g = open(phaseoutput, 'w')
    nn = 0
    nrms = float(nrms)
    ngap = int(ngap)
    maxdep = float(maxdep)

    with open(phaseinput, "r") as f:
        for line in f:
            if (len(line) == 68):
                iok = 0
                RMS = float(line[61:67])
                gap = int(line[54:57])
                dep = float(line[36:43])
                if RMS <= nrms and gap <= ngap and dep <= maxdep:
                    line = line.strip('\n')
                    nn = nn + 1
                    year = year0 + line[0:2]
                    mon = int(line[2:4])
                    day = int(line[4:6])
                    hour = int(line[7:9])
                    min = int(line[9:11])
                    sec = float(line[12:17])

                    if line[25] == 'N': #N
                        lat = float(line[18:25])
                    else:
                        lat = float(line[18:25]) * (-1)
                    if line[35] == 'E':
                        lon = float(line[27:35])
                    else:
                        lon = float(line[27:35]) * (-1)

                    dep = float(line[36:43])
                    mag = float(line[43:50])
                    EH = 0.00
                    EZ = 0.00
                    g.write(
                        '# {:4s} {:2d} {:2d} {:2d} {:2d} {:5.2f}  {:8.4f}  {:9.4f}  {:6.2f} {:5.2f} {:7.2f} {:7.2f} {:7.2f}      {:6d}\n'.format(
                            year, mon, day, hour, min, sec, lat, lon, dep, mag, EH, EZ, RMS, nn))
                    iok = 1
            else:
                if (iok == 1 and line[0] != '\n'):
                    line = line.strip('\n')
                    if (len(line) == 84):
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[0:6], float(line[8:14]), line[6]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[14:20], float(line[22:28]), line[20]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[28:34], float(line[36:42]), line[34]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[42:48], float(line[50:56]), line[48]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[56:62], float(line[64:70]), line[62]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[70:76], float(line[78:84]), line[76]))
                    if (len(line) == 70):
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[0:6], float(line[8:14]), line[6]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[14:20], float(line[22:28]), line[20]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[28:34], float(line[36:42]), line[34]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[42:48], float(line[50:56]), line[48]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[56:62], float(line[64:70]), line[62]))
                    if (len(line) == 56):
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[0:6], float(line[8:14]), line[6]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[14:20], float(line[22:28]), line[20]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[28:34], float(line[36:42]), line[34]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[42:48], float(line[50:56]), line[48]))
                    if (len(line) == 42):
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[0:6], float(line[8:14]), line[6]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[14:20], float(line[22:28]), line[20]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[28:34], float(line[36:42]), line[34]))
                    if (len(line) == 28):
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[0:6], float(line[8:14]), line[6]))
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[14:20], float(line[22:28]), line[20]))
                    if (len(line) == 14):
                        g.write('{:<5s}    {:8.3f}   1.000   {:1s}\n'.format(line[0:6], float(line[8:14]), line[6]))

    f.close()
    g.close()

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print('velest2hypoDD.py final.CNV hypoDD.pha rms_threhold gap_threshold maxdep')
        sys.exit()
    format_convert(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
