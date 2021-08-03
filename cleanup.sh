#!/bin/bash -w
#delete big files

#delete those dependent codes
#rm -rf src/FDTCC src/GrowClust src/HYPODD src/MatchLocate2 src/PhaseNet src/REAL src/hyp1.40 bin/*

#delete those generated big files
#Warning!!! you will delete all waveforms
rm -rf Data/waveform_sac
rm -rf Data/waveform_phasenet Data/waveform_mseed Data/fname.csv Data/station.dat Data/catalog.dat Data/*.jpg

rm -rf Pick/PhaseNet/20161014 Pick/PhaseNet/results
rm -rf Pick/STALTA/20161014

rm REAL/*.txt REAL/*.dat 
rm REAL/t_dist/*.pdf REAL/tt_db/ttdb.txt REAL/t_dist/t_dist.dat
rm -rf REAL/event_verify/*all REAL/event_verify/*pick

rm location/VELEST/*.cat location/VELEST/velest.* location/VELEST/man.OUT location/VELEST/out.CHECK location/VELEST/final.CNV location/VELEST/*.pdf location/VELEST/main.OUT
rm location/hypoinverse/*.arc location/hypoinverse/*.pdf location/hypoinverse/*.cat location/hypoinverse/*.crh
rm location/hypoinverse_corr/*.arc location/hypoinverse_corr/*.pdf location/hypoinverse_corr/*.cat location/hypoinverse_corr/*.crh location/hypoinverse_corr/*.del

rm hypoDD_dtct/hypoDD.reloc* hypoDD_dtct/hypoDD.pha hypoDD_dtct/dt.ct
rm hypoDD_dtcc/hypoDD.reloc* hypoDD_dtcc/hypoDD.pha hypoDD_dtcc/dt.cc
rm GrowClust/IN/hypoDD.pha GrowClust/IN/dt.cc GrowClust/OUT/out.* 

rm Magnitude/catalog_mag.txt

rm -rf MatchLocate/Template/2016* MatchLocate/Template/INPUT MatchLocate/20161014 MatchLocate/MultipleTemplate/waveforms MatchLocate/GrowClust/OUT/out.* MatchLocate/MultipleTemplate/DetectedFinal.dat MatchLocate/*.dat MatchLocate/INPUT.in
rm Plot/*.jpg Plot/*.pdf
