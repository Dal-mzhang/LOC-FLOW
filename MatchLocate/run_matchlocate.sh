#!/bin/bash -w
#Here provide a strategy for earthquake detection and location using template matching + GrowClust
#not well tested

#step 1#
#convert the catalog format  (as template)
#only keep events with large mag (e.g., 0.5)
cat ../GrowClust/OUT/out.growclust_cat |  awk '{if($11 > -1.5) printf"%4d/%02d/%02d %02d:%02d:%05.2f %7.4f %8.4f %6.2f M %5.2f\n",$1,$2,$3,$4,$5,$6,$8,$9,$10,$11}' > catalog_all.dat
#cat ../hypoDD_dtcc/hypoDD.reloc |  awk '{if($17 > 0.5) printf"%4d/%02d/%02d %02d:%02d:%05.2f %7.4f %8.4f %6.2f M %5.2f\n",$11,$12,$13,$14,$15,$16,$2,$3,$4,$17}' > catalog_all.dat
#cat ../hypoDD_dtct/hypoDD.reloc |  awk '{if($17 > 0.5) printf"%4d/%02d/%02d %02d:%02d:%05.2f %7.4f %8.4f %6.2f M %5.2f\n",$11,$12,$13,$14,$15,$16,$2,$3,$4,$17}' > catalog_all.dat
#cat ../REAL/catalogSA_allday.txt  |  awk '{if($10 > 0.5) printf"%4d/%02d/%02d %02d:%02d:%05.2f %7.4f %8.4f %6.2f M %5.2f\n",$1,$2,$3,$4,$5,$6,$7,$8,$9,$10}' > catalog_all.dat 
cat catalog_all.dat > catalog.dat # Use the first three templates as an example, not test the whole catalog.

#head -10 catalog_all.dat > catalog.dat # Use the first three templates as an example, not test the whole catalog.

#step 2#
#cut waveforms for templates, mark their P and S arrivals
#to make the demo time affortable, only use waveforms of vertical stations < 0.2 deg
#See marktaup.py
cd Template
rm -rf 201610*
python marktaup.py
cd ..

#step 3#
rm -rf 20161014
perl RunprocAll.pl catalog.dat
#we fiter both templates and continuous data in MatchLocate 
#(self-detection may be not exactly 1.0. a few reasons: 
#1.some phase segments may be zeros; 2. taper and fiter; 3. 0.01 sec sampling for the data
#the ideal way is to cut templates from filtered continuous data

#step 4#
cd MultipleTemplate
perl SelectFinal.pl 2016 10 14

#step 5#
cd ..
cd GrowClust/IN
perl gen_input_matchlocate.pl
cd ..
growclust growclust.inp

#step 6#
#check your results using the matlab script plot_3dscatter.m in GrowClust/OUT
