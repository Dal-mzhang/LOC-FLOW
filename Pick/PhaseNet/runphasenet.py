import warnings
import numpy as np
import pandas as pd
import shutil
import os

#os.system('conda activate phasenet') 
#If you didn't install phasenet in your base environment,
#please manually do this in your command line

#see cookbook step 1b
#####################step 1 ####################
# run phasenet to generate pick file picks.csv
print("################\nrun PhaseNet\n###############")
# Remove the previous directory
#if os.path.isdir("results"):
#    shutil.rmtree("results")
command = "python ../../src/PhaseNet/phasenet/predict.py --mode=pred --model_dir=../../src/PhaseNet/model/190703-214543 --data_dir=../../Data/waveform_phasenet --data_list=../../Data/fname.csv --format=mseed --amplitude"
print(command)
os.system(command)


#####################step 2####################
print("################\nseparate P and S picks\n###############")
# seperate the picks in picks.csv into p and s picks
pickfile = './results/picks.csv'
output1 = 'temp.p'
output2 = 'temp.s'
prob_threshold = 0.5
samplingrate = 0.01 #samplingrate of your data, default 100 hz

f = open(output1,'w')
g = open(output2,'w')
#data = pd.read_csv(pickfile)
data = pd.read_csv(pickfile,delimiter="\t")

sta = data['fname']
t0 = data['t0']
ppick_tmp = data['p_idx']
spick_tmp = data['s_idx']
pprob_tmp = data['p_prob']
sprob_tmp = data['s_prob']
p_amp = data['p_amp']
s_amp = data['s_amp']

for i in range(len(ppick_tmp)):
    year,mon,day,ss,net,name,pyz = sta[i].split('_')
    ss = float(ss)
    ppick = []
    spick = []
    pprob = []
    sprob = []
    pamp = []
    samp = []

    if len(ppick_tmp[i])>2:
        ppick_um = ppick_tmp[i][1:-1].split(',')
        pprob_um = pprob_tmp[i][1:-1].split(',')
        pamp_um = p_amp[i][1:-1].split(',')
        for j in range(len(ppick_um)):
            if ppick_um[j] != ',':
                ppick.append(ppick_um[j])
        for j in range(len(pprob_um)):
            if pprob_um[j] !=',':
                pprob.append(pprob_um[j])
        for j in range(len(pamp_um)):
            if pamp_um[j] !=',':
                pamp.append(pamp_um[j])

        for j in range(len(pprob)):
            if float(pprob[j]) >= prob_threshold:
                f.write('{},{},{},{},{},1,'.format(year,mon,day,net,name))
                tp = int(ppick[j])*samplingrate+ss
                #we cannot estimate the amplitude under the wood-anderson response
                #just roughly and empirically estimate it
                #to have more accurate magnitude, please re-calculate the magnitude after your get events
                #see calc_mag.py in Magnitude directory
                f.write('{},{},{}\n'.format(tp,pprob[j],float(pamp[j])*2080*20))

    if len(spick_tmp[i])>2:
        spick_um = spick_tmp[i][1:-1].split(',')
        sprob_um = sprob_tmp[i][1:-1].split(',')
        samp_um = s_amp[i][1:-1].split(',')
        for j in range(len(spick_um)):
            if spick_um[j] != ',':
                spick.append(spick_um[j])
        for j in range(len(sprob_um)):
            if sprob_um[j] !=',':
                sprob.append(sprob_um[j])
        for j in range(len(samp_um)):
            if samp_um[j] !=',':
                samp.append(samp_um[j])

        for j in range(len(sprob)):
            if float(sprob[j]) >= prob_threshold:
                g.write('{},{},{},{},{},1,'.format(year,mon,day,net,name))
                ts = int(spick[j])*samplingrate+ss
                #we cannot estimate the amplitude under the wood-anderson response
                #just roughly and empirically estimate it
                #to have more accurate magnitude, please re-calculate the magnitude after your get events
                #see calc_mag.py in Magnitude directory
                g.write('{},{},{}\n'.format(ts,sprob[j],float(samp[j])*2080*20))

    # Remove the previous directory
    pickfile=year+mon+day
    if os.path.isdir(pickfile):
        shutil.rmtree(pickfile)

#####################step 3####################
print("################\ncreat pick files by date and station name\n###############")
# separate picks based on date and station names
# the picks maybe not in order, it is fine and REAL
# will sort it by their arrival
command = "pick2real -Ptemp.p -Stemp.s"
print(command)
os.system(command)
os.remove(output1) 
os.remove(output2) 
