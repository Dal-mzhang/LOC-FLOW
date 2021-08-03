import os
import sys
import datetime

#Here we didn't consider depth above the sea level to avoid negative depth
#velocity model is relative to the average of station elevation
def model_format(modelin):
    output = 'vel_model_P.crh'  # velocity model
    gg = open(output, 'w')
    gg.write("MODEL Vp from REAL\n")
    kk = 0
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
        
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('mk_velmodel.py modelfile')
        sys.exit()
    model_format(sys.argv[1]) 
