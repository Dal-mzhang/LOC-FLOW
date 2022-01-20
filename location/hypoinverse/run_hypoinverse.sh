#!/bin/bash -w
phasein="phase_sel_all.txt"
stationin="../../Data/station.dat"
velocityin="../../REAL/tt_db/mymodel.nd"

####step 1 (cookbook 3.2 step 3a)##### create the velocity model, pay more attentation
python mk_velmodel.py $velocityin

#please run mk_velmodel.py to convert the Vp and Vs models
#maybe need to mannually adjust the velocities
#Note: the hypoinverse cannot allow two layers have the same velocity
#      and not allowed low velocity layer
#If you get consistent depths, you have this issue! 
#Slightly ajdust the model (e.g., increase vel a little bit with depth)

####step 2 (cookbook 3.2 step 3b)##### create the phase file
#merge REAL's phase file into one file
cat ../../REAL/*.phase_sel.txt > $phasein

python mk_inputfile.py $phasein $stationin > hypoinput.arc
rm $phasein

####step 3 (cookbook 3.2 step 3c)####### run hypoinverse
hyp1.40 <hyp.command
#hypoinverse cannot handle negative magnitude (manual, P48)
#negative magnitudes will be replaced by 0.0 here

####step 4 (cookbook 3.2 step 3d)####### run hypoinverse
###convert to readable format
nEH=5       #  horizontal uncertainty no larger than this
nEZ=5      #  vertical uncertainty no larger than this
ngap=300    #  station gap no larger than this
nrms=0.5    #  travetime residual no larger than this

python convertformat_outputfile.py hypoOut.arc new.cat dele.cat $nEH $nEZ $ngap $nrms
#Format: date, hh, mm, ss, lat, lon, dep, mag, rms, err_horizonal, err_dep, num
