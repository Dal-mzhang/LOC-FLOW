import sys
import linecache

def get_line_context(file_path, line_number):
    return linecache.getline(file_path, line_number).strip()

def decdeg2dms(dd):
    deg, mnt = divmod(dd*60.0, 60)
    return int(deg), mnt

def model_format(staCOR, staReal):
    output1 = 'P.del'  # velocity model for hypoinverse
    output2 = 'S.del'  # velocity model for hypoinverse
    #output3 = 'station.dat'  #station file for hypoinverse
    gg1 = open(output1, 'w')
    gg2 = open(output2, 'w')
    #hh = open(output3, 'w')
    ii = 1
    staNumber = len(open(staReal,"r").readlines())
    while ii <= staNumber:
        sta = get_line_context(staCOR, ii+1).split()[0]
        pdelay = float(get_line_context(staCOR, ii+1).split()[6])
        sdelay = float(get_line_context(staCOR, ii + 1).split()[7])
        net = get_line_context(staReal, ii).split()[2]
        latD, latM = decdeg2dms(float(get_line_context(staReal, ii).split()[1]))
        lonD, lonM = decdeg2dms(float(get_line_context(staReal, ii).split()[0]))
        eleva = int(float(get_line_context(staReal, ii).split()[5]) * 1000)
        ii = ii + 1
        gg1.write('{:5s} {:2s} {:5.2f}\n'.format(sta, net, pdelay))
        gg2.write('{:5s} {:2s} {:5.2f}\n'.format(sta, net, sdelay))
        #for channel in ['001', '002', '003']:
            #hh.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f} {:3d} {:7.4f}E{:4d}\n'.format(sta, net, channel, latD, latM, lonD, lonM, eleva))
            #hh.write('{:<5s} {:2s}  {:3s} {:3d} {:7.4f} {:3d} {:7.4f}E{:4d}       {:5d} {:5d}\n'.format(sta, net, channel, latD, latM,lonD, lonM, eleva, int(pdelay*100), int(sdelay*100)))
        
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('mk_stacorr.py sta.COR station_REAL.dat')
        sys.exit()
    model_format(sys.argv[1], sys.argv[2])
