#!/bin/bash -w
# Data preparation and phase picking may take a lot of time
# please type "conda activate phasenet" in the command line first
# obspy is included in phasenet

#downloading will take minutes for one-hour data 
# (MacBook Pro, 2.9 Ghz, 6-Core Intel Core i9, 32 GB)
start=`date +%s`
###########################in Data dir#################
irun=0 #0: no, do nothing
       #1: yes,run this step

if (($irun == 1))
then
    #data download
    cd Data
    echo 'downloading the data'
    python waveform_download_mseed.py || { echo 'Error in data download'; exit 1; }
    #python waveform_download.py (station_all.dat is required, slow)

    echo 'converting the data'
    #data format conversion
    python phasenet_input.py || { echo 'Error in data conversion'; exit 1; }
    #take tens of seconds or a few minitues
    cd ..
else
    echo 'Data download step skipped'
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
        python trigger_p_amp.py || { echo 'Error in P-wave picking'; exit 1; }
        python trigger_s_amp.py || { echo 'Error in S-wave picking'; exit 1; }
        cd ../../
    elif (($picker == 1))
    then
        #run PhaseNet and creat REAL required pick files
        cd ./Pick/PhaseNet
        #conda activate phasenet 
        #You have to manually activate the python environment before run the script
        python runphasenet.py || { echo 'Error running PhaseNet'; exit 1; }
        sleep 0.5
        cd ../../
    else
        echo 'please select your picker'
        exit 1
    fi
else
    echo 'Picking step skipped'
fi

#association will take a few mintues
#which depends on the parameter setting and study region
#########################in REAL dir#################
ittable=0 #0: don't build the travel time table
          #1: build the travel time table (run once, then turn it off)
ireal=1   #0: no, do nothing
          #1: yes,run REAL association

if (($ittable == 1)) 
then
    echo 'building traveltime table ...'
    cd ./REAL/tt_db
    # create travel time table
    python taup_tt.py || { echo 'Error building travel time table'; exit 1; }
    cd ../../
else
    echo 'Travel time table building step skipped'
fi

if (($ireal == 1)) 
then
    cd ./REAL/
    # run REAL and merge picks and catalogs
    perl runREAL.pl $picker || { echo 'Error running REAL'; exit 1; }
    cd ..
    # please check the X-T curves for P and S in the t_dist dir
    # please check waveforms and picks to verify those worst events in the event_verify dir
    # based on their performance, ajdust your parameters in runREAL.pl
else
    echo 'REAL association step skipped'
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
    bash run_velest.sh $mode || { echo 'Error running VELEST'; exit 1; }
    cd ../..

elif (($hypo == 2))
then
    echo 'hypoinverse location ...'
    cd hypoinverse
    bash run_hypoinverse.sh || { echo 'Error running Hypoinverse'; exit 1; }
    #velocity model is tricky, may need to mannually adjust it.
    cd ../..
elif (($hypo == 3))
then
    echo 'VELEST first, hypoinverse second'
    cd VELEST
    mode=0
    bash run_velest.sh $mode || { echo 'Error running VELEST in mode 0'; exit 1; }
    cd ../hypoinverse_corr
    bash run_hypoinverse_corr.sh || { echo 'Error running Hypoinverse with VELEST corrections'; exit 1; }
    #velocity model is tricky, check notices in run_hypoinverse_corr.sh.
    cd ../..
else
    echo 'please select your location method'
    exit 1
fi

#########################in hypoDD_dtct dir#################
cd hypoDD_dtct
bash run_hypoDD_dtct.sh $hypo || { echo 'Error running hypoDD_dtct'; exit 1; }
# may need to change parameters in ph2dt.in and hypoDD.in
cd ../

#########################in hypoDD_dtcc dir#################
#please make sure you have finished hypoDD_dtct
#here we use hypoDD_dtct locations to update those available
#locations from hypoDD_dtct, others are kept as the initial 
#locations. Just provide a strategy, feel free to change
cd hypoDD_dtcc
bash run_hypoDD_dtcc.sh || { echo 'Error running hypoDD_dtcc'; exit 1; }
# may need to change parameters in ph2dt.in and hypoDD_cconly.inp
cd ..

#########################in GrowClust dir#################
#please make sure you have finished hypoDD_dtct
#here we use hypoDD_dtct locations to update those available
#locations from hypoDD_dtct, others are kept as the initial 
#locations. Just provide a strategy, feel free to change
cd ./GrowClust
bash run_growclust.sh || { echo 'Error running GrowClust'; exit 1; }
cd ..

#show preliminary location figures
cd Plot
bash plot_3dgmt.sh || { echo 'Error plotting 3D GMT'; exit 1; }
cd ..

#--------------------------optional-----------------------
##########################in Magintude dir###############
#An exmaple showing how to re-calculate local magnitude
#Just an example, feel free to change as needed
#cd Magnitude
#python calc_mag.py || { echo 'Error calculating magnitude'; exit 1; }
#cd ..

##########################in MatchLocate dir###############
#An example showing how to use template events from GrowClust or others
#newly detected events will be relocated by growclust
#see MatchLocate/GrowClust/OUT/out.growclust_cat
#Just provide a strategy, not well tested
#cd MatchLocate
#bash run_matchlocate.sh || { echo 'Error running MatchLocate'; exit 1; }

end=`date +%s`
echo 'total time' $((end-start)) 'sec'
