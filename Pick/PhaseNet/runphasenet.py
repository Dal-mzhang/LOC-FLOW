import warnings
import numpy as np
import pandas as pd
import shutil
import os
from datetime import datetime

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
command = "python ../../src/PhaseNet/phasenet/predict.py --mode=pred --model_dir=../../src/PhaseNet/model/190703-214543 --data_dir=../../Data/waveform_sac --data_list=../../Data/fname.csv --format=sac --highpass_filter=1 --amplitude"
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
data = pd.read_csv(pickfile, parse_dates=["begin_time", "phase_time"])
data = data[data["phase_score"] >= prob_threshold].reset_index(drop=True)

data[["year", "mon", "day"]] = data["begin_time"].apply(lambda x: pd.Series([f"{x.year:04d}", f"{x.month:02d}", f"{x.day:02d}"]))
data["ss"] = data["begin_time"].apply(lambda x: (x - datetime.fromisoformat(f"{x.year:04d}-{x.month:02d}-{x.day:02d}")).total_seconds())
data[["net", "name", "channel"]] = data["station_id"].apply(lambda x: pd.Series(x.split(".")))
data["dum"] = pd.Series(np.ones(len(data)))
data["phase_amp"] = data["phase_amp"] * 2080 * 20
data["phase_time"] = data["ss"] + data["phase_index"] * samplingrate
data[data["phase_type"] == "P"].to_csv(output1, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)
data[data["phase_type"] == "S"].to_csv(output2, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)

for i in range(len(data["file_name"])):
    (pickfile,junk) = data["file_name"][i].split('/')
    if os.path.isdir(pickfile):
        shutil.rmtree(pickfile)
#####################step 3####################
print("################\ncreat pick files by date and station name\n###############")
# separate picks based on date and station names
# the picks maybe not in order, it is fine and REAL
# will sort it by their arrival
command = "pick2real -Ptemp.p -Stemp.s &"
print(command)
os.system(command)
#os.remove(output1) 
#os.remove(output2) 
