import os
import sys
import datetime
import linecache

#Here we didn't consider depth above the sea level to avoid negative depth
#velocity model is relative to the average of station elevation

def get_line_context(file_path, line_number):
    return linecache.getline(file_path, line_number).strip()

def model_format(modelin):
    output = 'vel_model_P.crh'  # velocity model
    gg = open(output, 'w')
    gg.write("MODEL Vp from REAL\n")
    kk = 0
    i=0
    with open(modelin, "r") as f:
        for line in f:
            line = line.strip('\n')
            dep = line.split()[0]
            if dep == 'mantle':
                kk = 1
            if kk == 0:
                dep = float(dep)
                vp = float(line.split()[1])
                gg.write('{:4.2f}  {:5.2f}\n'.format(vp, dep))
                i=i+1
    line_more = get_line_context(modelin, i+2)
    dep = line_more.split()[0]
    dep_1 = float(dep) + 0.1 # HYPOINVERSE doesn't like the same depth
    vp_1 = float(line_more.split()[1])
    vs_1 = float(line_more.split()[2])
    gg.write('{:4.2f}  {:5.2f}\n'.format(vp_1, dep_1)) # include the upper mantle layer

    output = 'vel_model_S.crh'  # velocity model
    gg = open(output, 'w')
    gg.write("MODEL Vs from REAL\n")
    kk = 0
    with open(modelin, "r") as f:
        for line in f:
            line = line.strip('\n')
            dep = line.split()[0]
            if dep == 'mantle':
                kk = 1
            if kk == 0:
                dep = float(dep)
                vs = float(line.split()[2])
                gg.write('{:4.2f}  {:5.2f}\n'.format(vs, dep))
    gg.write('{:4.2f}  {:5.2f}\n'.format(vs_1, dep_1)) # include the upper mantle layer 
        
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('mk_velmodel.py modelfile')
        sys.exit()
    model_format(sys.argv[1]) 
