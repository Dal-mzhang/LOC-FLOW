import sys
from itertools import islice
import linecache

def get_line_context(file_path, line_number):
    return linecache.getline(file_path, line_number).strip()

def model_format(modelin):
    output1 = 'vel_model_P.crh'  # velocity model
    output2 = 'vel_model_S.crh'  # velocity model
    gg = open(output1, 'w')
    hh = open(output2, 'w')
    gg.write("MODEL Vp Output by isingle = 0 in VELEST\n")
    hh.write("MODEL Vs Output by isingle = 0 in VELEST\n")
    layers = get_line_context(modelin, 2)
    kk = 1
    input_file = open(modelin)
    for line in islice(input_file, 2, None):  # start from the third line
        line = line.strip('\n')
        begin = line.split()[0]
        if begin != layers and kk == 1:
            vp = float(line.split()[0])
            dep = float(line.split()[1])
            if dep >= 0:
                gg.write('{:4.2f}  {:5.2f}\n'.format(vp, dep))
        else:
            kk = 2
        if kk == 2 and len(line) > 5:
            vs = float(line.split()[0])
            dep = float(line.split()[1])
            if dep >= 0:
                hh.write('{:4.2f}  {:5.2f}\n'.format(vs, dep))
        
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('mk_vel_velest2hypoinverse.py modelfile')
        sys.exit()
    model_format(sys.argv[1]) 
