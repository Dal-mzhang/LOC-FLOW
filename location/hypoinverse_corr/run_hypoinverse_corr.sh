#!/bin/bash -w
phasein="phase_sel_all.txt"
stationin="../../Data/station.dat"
velest_sta_corr="../VELEST/velest.sta" #velest's output (mode=0 only), renamed.
velest_vel="../VELEST/velest.mod" #velest's output (mode=0), renamed.

###only eligible to have enough reliable events to update vel. and sta. corr.in the VELEST step###
###you will get worse locations if your vel. and sta. corr. are not updated properly.

####step 1 (cookbook 3.3 step 3a)##### create station delay files and velocity model
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

cat hypoOut.arc|gawk '{if(substr($0,1,4) == 2016)print substr($1,1,4),substr($1,5,2),substr($1,7,2),substr($1,9,2),substr($1,11,2),substr($1,13,4)/100,substr($1,17,2)+substr($0,20,4)/6000,substr($0,24,3)+substr($0,28,4)/6000,substr($0,33,4)/100,substr($0,124,3)/100,substr($0,49,4)/100,substr($0,86,4)/100,substr($0,90,4)/100, substr($0,43,3), substr($0,49,4)/100}'|awk '{if ($12<='"$nEH"' && $13<='"$nEZ"' && $14<='"$ngap"' && $15<='"$nrms"') {printf "%4s%2s%2s %2d %2d %5.2f %7.4f %8.4f %5.2f %5.2f %5.2f %5.2f %5.2f %d\n",$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,NR}}' > new.cat

cat hypoOut.arc|gawk '{if(substr($0,1,4) == 2016)print substr($1,1,4),substr($1,5,2),substr($1,7,2),substr($1,9,2),substr($1,11,2),substr($1,13,4)/100,substr($1,17,2)+substr($0,20,4)/6000,substr($0,24,3)+substr($0,28,4)/6000,substr($0,33,4)/100,substr($0,124,3)/100,substr($0,49,4)/100,substr($0,86,4)/100,substr($0,90,4)/100, substr($0,43,3), substr($0,49,4)/100}'|gawk '{if ($12<='"$nEH"' && $13<='"$nEZ"' && $14<='"$ngap"' && $15<='"$nrms"') {} else {printf "%4s%2s%2s %2d %2d %5.2f %7.4f %8.4f %5.2f %5.2f %5.2f %5.2f %5.2f %d\n",$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,NR}}' > dele.cat

#Format: date, hh, mm, ss, lat, lon, dep, mag, rms, err_horizonal, err_dep, num
