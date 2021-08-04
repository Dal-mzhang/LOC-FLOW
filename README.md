# LOC-FLOW
Earthquake Location Workflow

![LOC-FLOW](https://user-images.githubusercontent.com/51533859/127945778-3c260000-b597-4377-9285-fb7da432c1c6.jpg)

LOC-FLOW is an “hands-free” earthquake location workflow to process continuous seismic records: from raw waveforms to well located earthquakes with magnitude calculations. The package assembles several popular routines for sequential earthquake location refinements, suitable for catalog building ranging from local to regional scales. 

The LOC-FLOW is released and maintained at https://github.com/Dal-mzhang/LOC-FLOW.

How to start? bash run_all.sh. 
Detailed step-by-step explanations can be found in the CookBook and corresponding scripts.

Dependent packages in LOC-FLOW includes PhaseNet [contains Obspy], REAL, VELEST, HYPOINVERSE, hypoDD, GrowClust, FDTCC, Match&Locate; see [STEP 0 in the CookBook or src]. Questions related to the original packages should be addressed to the corresponding authors.

All other credits to Miao Zhang (also author of REAL and Match&Locate), Min Liu (also author of FDTCC), and Tian Feng, who integrated these packages and made the I/O codes publicly available. We thank Weiqiang Zhu for help with the PhaseNet. The CookBook is prepared by Ruijia Wang and Miao Zhang.

Users are free to make modifications to the programs to meet their particular needs, but are discouraged from distributing modified code to others without notification of the authors. If you find any part of the workflow useful, please cite our work or the corresponding publications of the packages.

Questions and comments? Email Miao Zhang (miao.zhang@dal.ca)                                                                      
