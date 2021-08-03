#!/bin/bash -w
# input 1: location alone
#       0: location + model + sta. corr.
((!$#)) && echo bash $0 0,1 && exit 1
######################## step 1 (cookbook 3.2, 3a) ##################
# change parameters as needed
lat=42.75 # reference latitude
lon=13.25 # reference longitude 
distmax=120 # largest distance (stations with larger distance will be neglected) 
mode=$1 # 1: update locations alone (fast, usually good enough for your study) 
           # 0: first udpate locations and velocitiy using high-quanlity events and picks
           #    second relocate all events (slow, only for specific analysis), 

station=../../Data/station.dat # station direcotry
vel=../../REAL/tt_db/mymodel.nd # velocity model directory
phasein_best=../../REAL/phase_best_allday.txt # use the SA locations (for mode = 0 only)
phasein=../../REAL/phase_allday.txt # use the relocated SA locations

####################### step 2 (cookbook 3.2, 3b)#####################
# run velest with different options
if (($mode == 1))
then
    # location alone
    # prepare the required phase file, velocity file, station file, and velest control file following VELEST's format
    perl convertformat.pl $lat $lon $distmax $mode $station $vel $phasein
    echo perl convertformat.pl $lat $lon $distmax $mode $station $vel $phasein
    # run velest
    velest
elif (($mode == 0))
then
    # 1. update location, velocity, station correction using high-quanlity events and picks
    # please go to convertformat.pl and change the vel and sta. corr. damping following the VELEST manual
    perl convertformat.pl $lat $lon $distmax $mode $station $vel $phasein_best
    # run velest, adjust parameters in covertformat.pl following velest's manual
    velest
    # 2. run velest to locate all events using updated velocity model
    perl convertformat.pl $lat $lon $distmax 1 $station $vel $phasein
    mv sta.COR velest.sta # replace the station file (now you have updated station correction)
    mv velest.mod velest.mod.org # copy your original velocity model
    mv velout.mod velest.mod # replace your original velocity model by the updated model
    # run velest
    velest
else
   echo 'please choose your location mode 0 or 1'
   echo 'bash run_velest.sh 0 or 1'
   exit
fi

####################### step 3 (cookbook 3.2, 3c)###################
# result format conversion and reselection
stationgap=300 # events with station gap larger than this will be discarded
resmax=0.5 # events with travel time residual larger than this will be discarded
relocatalog=new.cat # kept relocations
deletedcatalog=dele.cat # discarded relocations
# convert output location format
perl convertoutput.pl $stationgap $resmax $relocatalog $deletedcatalog
#Format: date, hh, mm, ss, lat, lon, dep, mag, station gap, res, num

wc -l initial.cat | awk '{ printf "before selection: %d events\n",$1}'
wc -l new.cat | awk '{ printf "after selection: %d events\n",$1}'
