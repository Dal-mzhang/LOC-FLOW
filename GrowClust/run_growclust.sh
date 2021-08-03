#!/bin/bash  -w

##########step 1 (step 5a)###########
#go to the IN dir and create required inputs
cd IN
perl gen_input.pl

#########step 2 (step 5b)###########
#run growclust
cd ..
growclust growclust.inp
