#!/bin/bash -w
((!$#)) && echo bash $0 0,1,2,3 && exit 1
phaseout=hypoDD.pha; #phase format for hypoDD
stationin=../Data/station.dat; #station list
stationout=station.dat; #station format by hypoDD

awk '{print($4,$2,$1)}' $stationin > $stationout

hypo=$1 #from your input

#########################step 1 (4a in cookbook)########################
#hypo=0 # use REAL's simulated annealing location
#hypo=1 # use velest location
#hypo=2 # use hypoinverse location
#hypo=3 # use hypoinverse_corr location

rm $phaseout #delete previous phase file

if (($hypo == 0))
then    
        cp ../REAL/phaseSA_allday.txt $phaseout
elif (($hypo == 1))
then
        rms_threshold=0.5 # in sec, events with rms larger than this will not be used
        gap_threshold=300 # in deg., events with station gap larger than this will not be used
        maxdep=20 # in km, events with larger depth will not be used (< dep in the timetable)
        phasein=../location/VELEST/final.CNV
        python velest2hypoDD.py $phasein $phaseout $rms_threshold $gap_threshold $maxdep
        echo python velest2hypoDD.py $phasein $phaseout $rms_threshold $gap_threshold $maxdep
elif (($hypo == 2))
then
        phasein="../location/hypoinverse/hypoOut.arc"
        rms_threshold=0.5 # in sec, events with rms larger than this will not be used
        gap_threshold=300 # in deg., events with station gap larger than this will not be used
        pick_nres=3       # if pick's residual larger than nres times event's rms
                          # the pick will not be used
        maxdep=20 # in km, events with larger depth will not be used (< dep in the timetable)
        maxdep_err=5 # in km, events with larger depth uncertainty will not be used
        maxdis_err=5 # in km, events with larger horizontal uncertainty will not be used
        python hypoinverse2hypoDD.py $phasein $phaseout $rms_threshold $gap_threshold $pick_nres $maxdep $maxdep_err $maxdis_err
        echo python hypoinverse2hypoDD.py $phasein $phaseout $rms_threshold $gap_threshold $pick_nres $maxdep $maxdep_err $maxdis_err
elif (($hypo == 3))
then
        phasein="../location/hypoinverse_corr/hypoOut.arc"
        rms_threshold=0.5 # in sec, events with rms larger than this will not be used
        gap_threshold=300 # in deg., events with station gap larger than this will not be used
        pick_nres=3       # if pick's residual larger than nres times event's rms
                          # the pick will not be used
        maxdep=20 # in km, events with larger depth will not be used (< dep in the timetable)
        maxdep_err=5 # in km, events with larger depth uncertainty will not be used
        maxdis_err=5 # in km, events with larger horizontal uncertainty will not be used
        python hypoinverse2hypoDD.py $phasein $phaseout $rms_threshold $gap_threshold $pick_nres $maxdep $maxdep_err $maxdis_err
        echo python hypoinverse2hypoDD.py $phasein $phaseout $rms_threshold $gap_threshold $pick_nres $maxdep $maxdep_err $maxdis_err
else
        echo 'please select your location resources: 0, 1, 2, 3'
        exit
fi

#########################step 2 (4b in cookbook)########################
rm dt.ct
ph2dt ph2dt.inp

#########################step 3 (4c in cookbook)########################
hypoDD hypoDD.inp
