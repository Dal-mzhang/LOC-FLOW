#!/bin/bash -w
#please finish hypoDD_dtct first before you start hypoDD_dtcc
#to have accuarte initial locations for dtcc
#we use dtct locations to update the phase file
phasein=../hypoDD_dtct/hypoDD.pha #phase file used in hypoDD_dtct
relocation=../hypoDD_dtct/hypoDD.reloc #locations in hypoDD_dtct
phaseout=./hypoDD.pha; #phase format for hypoDD
stationin=../Data/station.dat; #station list
stationout=station.dat; #station format by hypoDD

awk '{print($4,$2,$1)}' $stationin > $stationout

##############################step 1 (cookbook 5a)#####################
#generate a new hypoDD.pha for hypoDD (dt.cc)
useall=1  #0: only use those well-located events from hypoDD.reloc (dt.ct)
          #1: update available event locations from hypoDD.reloc (dt.ct)
          #   others will be kept as the same as that in $phasein
perl updatephase.pl $phasein $relocation $phaseout $useall


##############################step 2 (cookbook 5b)#####################
rm dt.ct
ph2dt ph2dt.inp

##################################################################################################
# create the dt.cc file from continuous SAC files or event segments

#-----------------------------Parameters setting-----------------------------
#waveform window length before and after trigger
#
#  -------|-----------|------------------|------
#             (wb)   pick      (wa)
# For P phase CC, if your "wa" is larger than 0.9*(ts-tp), it will be replaced
# by 0.9*(ts-tp) to make sure you don't include S phase.
# For S phase CC, if your "wb" is larger than 0.5*(ts-tp), it will be replaced
# by 0.5*(ts-tp) to make sure you don't include P phase.
#waveform window length before and after picks and their maximum shift length
W=1.0/1.0/0.3/1.0/1.5/0.5
#sampling interval, CC threshold, SNR threshold, maximum abs(t1-t2) of the two picks
D=0.01/0.6/1/2
#ranges and grids in horizontal direction and depth (in traveltime table)
G=1.4/20/0.01/1
#specify the path of event.sel, dt.ct and phase.dat (1: yes, 0: default names)
C=1/1/1
#input data format (-3: continuous data -5: event segments)
F=-3
#BP filter, low and high B=-1/-1 will not fiter the data 
B=2/8

staDir=../Data/station.dat
tttDir=../REAL/tt_db/ttdb.txt
wavDir=../Data/waveform_sac
eveDir=./event.sel
dctDir=./dt.ct
paDir=$phaseout

rm dt.cc
FDTCC -F$F -B$B -C$C -W$W -D$D -G$G $staDir $tttDir $wavDir $eveDir $dctDir $paDir
echo FDTCC -F$F -B$B -C$C -W$W -D$D -G$G $staDir $tttDir $wavDir $eveDir $dctDir $paDir
rm Input*

##############################step 3 (cookbook 5c)#####################
hypoDD hypoDD_cconly.inp

