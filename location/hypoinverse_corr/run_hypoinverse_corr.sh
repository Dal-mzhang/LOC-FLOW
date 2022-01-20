#!/bin/bash -w
phasein="phase_sel_all.txt"
stationin="../../Data/station.dat"
velest_sta_corr="../VELEST/velest.sta" #velest's output (mode=0 only), renamed.
velest_vel="../VELEST/velest.mod" #velest's output (mode=0), renamed.

###only eligible to have enough reliable events to update vel. and sta. corr.in the VELEST step###
###you will get worse locations if your vel. and sta. corr. are not updated properly.

####step 1 (cookbook 3.3 step 3a)##### create velocity model
python mk_vel_velest2hypoinverse.py $velest_vel

#please run mk_vel_velest2hypoinverse.py to convert the Vp and Vs models
#may need to mannually adjust the velocities
#Note: the hypoinverse cannot allow two layers have the same velocity, 
#      and not allowed low velocity layer
#If you get consistent depths, you have this issue! 
#Slightly ajdust the model (e.g., increase vel a little bit with depth)

####step 2 (cookbook 3.3 step 3b)##### create the phase file
#merge REAL's phase file into one file
cat ../../REAL/*.phase_sel.txt > $phasein
python mk_inputfile.py $phasein $stationin > hypoinput.arc
rm $phasein

# create station delay files
python mk_stacorr.py $velest_sta_corr $stationin

####step 3 (cookbook 3.3 step 3c)####### run hypoinverse
hyp1.40 <hyp.command
#hypoinverse cannot handle negative magnitude (manual, P48)
#negative magnitudes will be replaced by 0.0 here

####step 4 (cookbook 3.3 step 3d)####### run hypoinverse
###convert to readable format
nEH=5       #  horizontal uncertainty no larger than this
nEZ=5      #  vertical uncertainty no larger than this
ngap=300    #  station gap no larger than this
nrms=0.5    #  travetime residual no larger than this

python convertformat_outputfile.py hypoOut.arc new.cat dele.cat $nEH $nEZ $ngap $nrms
#Format: date, hh, mm, ss, lat, lon, dep, mag, rms, err_horizonal, err_dep, num
