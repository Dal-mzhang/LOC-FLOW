#!/bin/bash -w

#download software
#python software_download.py

#hypoinverse has to be downloaded seperately at https://www.usgs.gov/software/hypoinverse-earthquake-location
#you need to manually download it

#manually go to every software dir and compile them
#compliers in their Makefile may be changed as needed
#For phasenet, please install it to "phasenet" virtual envirionment
#conda env create -f env.yml

#build the bin dir
mkdir ../bin

#move commands into ../bin
cp ./FDTCC/bin/FDTCC ../bin/            #need SAC lib in Makefile
cp ./GrowClust/SRC/growclust ../bin/    
cp ./HYPODD/src/hypoDD/hypoDD ../bin/   #change g77 to gfortran or similar complier
cp ./HYPODD/src/ph2dt/ph2dt ../bin/     #change g77 to gfortran or similar complier
cp ./MatchLocate2/bin/* ../bin/         #need SAC lib in Makefile
cp ./REAL/bin/* ../bin/                 #change gcc-10 (on Mac) to gcc as needed
cp ./hyp1.40/source/hyp1.40  ../bin     #change f77 to gfortran or similar complier

#add this commond in your ~/.bash_profile or ~/.bashrc
#export PATH=${your path}/LOCFLOW/bin/:$PATH
#e.g., export PATH=/Users/miao/Desktop/LOCFLOW/bin:$PATH

#in your command line
#source ~/.bash_profile
