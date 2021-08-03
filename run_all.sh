#!/bin/bash -w
# Data preparation and phase picking may take a lot of time
# please type "conda activate phasenet" in the command line first
# obspy is included in phasenet

#downloading will take minutes for one-hour data 
# (MacBook Pro, 2.9 Ghz, 6-Core Intel Core i9, 32 GB)
start=`date +%s`
###########################in Data dir#################
irun=1 #0: no, do nothing
       #1: yes,run this step

if (($irun == 1))
then
    #data download
    cd Data
    echo 'downloading the data'
    python waveform_download_mseed.py 
    #python waveform_download.py (station_all.dat is required, slow)

    echo 'converting the data'
    #data format conversion
    python phasenet_input.py 
    #take tens of seconds or a few minitues
cd ..
fi

#picking will take a few mintues
#########################in Pick dir#################
ipick=1  #0: no, do nothing
         #1: yes,run this step
picker=1 #0: STA/LTA picker
         #1: phasenet picker

if (($ipick == 1))
then
        echo 'picking ...'
    if (($picker == 0)) 
    then
        #run recursive_sta_lta and creat REAL required pick files
        cd ./Pick/STALTA
        python trigger_p_amp.py
        python trigger_s_amp.py
        cd ../../
    elif (($picker == 1))
    then
        #run PhaseNet and creat REAL required pick files
        cd ./Pick/PhaseNet
        #conda activate phasenet 
        #You have to manually activate the python environment before run the script
        python runphasenet.py
        cd ../../
    else
        echo 'please select your picker'
        exit
    fi
fi

#association will take a few mintues
#which depends on the parameter setting and study region
#########################in REAL dir#################
ittable=1 #0: don't build the travel time table
          #1: build the travel time table (run once, then turn it off)
ireal=1   #0: no, do nothing
          #1: yes,run REAL association

if (($ittable == 1)) 
then
    echo 'building traveltime table ...'
    cd ./REAL/tt_db
    # create travel time table
    python taup_tt.py
    cd ../../
fi

if (($ireal == 1)) 
then
    cd ./REAL/
    # run REAL and merge picks and catalogs
    perl runREAL.pl $picker
    cd ..
    # please check the X-T curves for P and S in the t_dist dir
    # please check waveforms and picks to verify those worst events in the event_verify dir
    # based on their performance, ajdust your parameters in runREAL.pl
fi

#########################in location dir#################
hypo=2  # 0: use the REAL's simulated annealing locations
        # 1: use VELEST locations (mode=1: location; mode=0: location + sta. corr. + vel update; 
        #                          mode=0 only for high-quanlity large datset)
        # 2. use hypoinverse locations, recommend this one!!
        # 3. use VELEST updated vel. and sta. as hypoinverse's input 
        #    (only for large dataset in VELEST mode=0)

#If hypo=1 i.e., VELEST location, please select which mode will be used. mode=1 is recommended.
mode=1  #1: update location alone (default)
        #0: use high quanlity events to update velcity, location, station corr.
        #   then relocate all events. use mode=0 only for many events!!

cd location

if (($hypo == 0))
then
     # do nothing, already done in REAL
     echo 'use REAL SA location'
     cd ..
elif (($hypo == 1))
then
    echo 'VELEST location ...'
    cd VELEST
    bash run_velest.sh $mode
    cd ../..

elif (($hypo == 2))
then
    echo 'hypoinverse location ...'
    cd hypoinverse
    bash run_hypoinverse.sh 
    #velocity model is tricky, may need to mannually adjust it.
    cd ../..
elif (($hypo == 3))
then
    echo 'VELEST first, hypoinverse second'
    #newly developed, not well tested
    cd VELEST
    mode=0
    bash run_velest.sh $mode
    cd ../hypoinverse_corr
    bash run_hypoinverse_corr.sh 
    #velocity model is tricky, check notices in run_hypoinverse_corr.sh.
    cd ../..
else
    echo 'please select your location method'
    exit
fi

#########################in hypoDD_dtct dir#################
cd hypoDD_dtct
bash run_hypoDD_dtct.sh $hypo 
# may need to change parameters in ph2dt.in and hypoDD.in
cd ../

#########################in hypoDD_dtcc dir#################
#please make sure you have finished hypoDD_dtct
#here we use hypoDD_dtct locations to update those available
#locations from hypoDD_dtct, others are kept as the initial 
#locations. Just provide a strategy, feel free to change
cd hypoDD_dtcc
bash run_hypoDD_dtcc.sh
# may need to change parameters in ph2dt.in and hypoDD_cconly.inp
cd ..

#########################in GrowClust dir#################
#please make sure you have finished hypoDD_dtct
#here we use hypoDD_dtct locations to update those available
#locations from hypoDD_dtct, others are kept as the initial 
#locations. Just provide a strategy, feel free to change
cd ./GrowClust
bash run_growclust.sh
cd ..

#--------------------------optional-----------------------
##########################in Magintude dir###############
#An exmaple showing how to re-calculate local magnitude
#Just an example, feel free to change as needed
#cd Magnitude
#python calc_mag.py

##########################in MatchLocate dir###############
#An example showing how to use template events from GrowClust or others
#newly detected events will be relocated by growclust
#Just provide a strategy, not well tested
#cd MatchLocate
#bash run_matchlocate.sh

end=`date +%s`
echo 'total time' $((end-start)) 'sec'
