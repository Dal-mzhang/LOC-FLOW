# LOC-FLOW
Earthquake Location Workflow

![LOCFLOW](https://user-images.githubusercontent.com/51533859/157482787-af57edf4-a2da-48c8-b1f3-090c48bd3bbf.jpg)

LOC-FLOW is an “hands-free” earthquake location workflow to process continuous seismic records: from raw waveforms to well located earthquakes with magnitude calculations. The package assembles several popular routines for sequential earthquake location refinements, suitable for catalog building ranging from local to regional scales. DOI:10.5281/zenodo.5875084

The LOC-FLOW is released and maintained at https://github.com/Dal-mzhang/LOC-FLOW.

How to start? bash run_all.sh. 
Detailed step-by-step explanations can be found in the CookBook and corresponding scripts.

Dependent packages in LOC-FLOW include PhaseNet [contains Obspy], REAL, VELEST, HYPOINVERSE, hypoDD, GrowClust, FDTCC, Match&Locate; see [STEP 0 in the CookBook or src]. Questions related to the original packages should be addressed to the corresponding authors.

All other credits to Miao Zhang (also author of REAL and Match&Locate), Min Liu (also author of FDTCC), and Tian Feng, who integrated these packages and made the I/O codes publicly available. We thank Weiqiang Zhu for help with the PhaseNet. The CookBook is prepared by Ruijia Wang and Miao Zhang.

Users are free to make modifications to the programs to meet their particular needs, but are discouraged from distributing modified code to others without notification of the authors. If you find any part of the workflow useful, please cite our work or the corresponding publications of the packages.

Please download (src/software_download.py) and regularly check source code updates: PhaseNet: https://github.com/wayneweiqiang/PhaseNet; REAL: https://github.com/Dal-mzhang/REAL; FDTCC: https://github.com/MinLiu19/FDTCC; hypoDD: https://www.ldeo.columbia.edu/~felixw/hypoDD.html; GrowClust: https://github.com/dttrugman/GrowClust; Match&Locate: https://github.com/Dal-mzhang/MatchLocate2; HYPOINVERSE: https://www.usgs.gov/node/279394 or https://faldersons.net/Software/Hypoinverse/Hypoinverse.html

A Chinese tutorial at https://drive.google.com/file/d/1zlaubeYgmQnBeCO9dz627HXrtrwy79rm/view?usp=sharing (recorded video at https://www.koushare.com/video/videodetail/14767)

Questions and comments? Email Miao Zhang (miao.zhang@dal.ca)                                                                      

References:

LOC-FLOW, FDTCC:  
Zhang M., M. Liu, T. Feng, R. Wang, and W. Zhu. LOC-FLOW: An End-to-End Machine-Learning-Based High-Precision Earthquake Location Workflow, Seismol. Res. Lett., 2022, doi: 10.1785/0220220019.

PhaseNet:  
Zhu, W., and G. C. Beroza (2019). PhaseNet : A deep-neural-networkbased seismic arrival-time picking method, Geophys. J. Int. 216, no. 1, 261–273, doi: 10.1093/gji/ggy423.  

REAL:  
Zhang, M., W. L. Ellsworth, and G. C. Beroza (2019). Rapid earthquake association and location, Seismol. Res. Lett. 90, no. 6, 2276–2284, doi: 10.1785/0220190052.  

VELEST:  
Kissling, E., W. L. Ellsworth, D. Eberhart-Phillips, and U. Kradolfer (1994). Initial reference models in local earthquake tomography, J. Geophys. Res. 99, no. B10, 19,635–19,646, doi: 10.1029/93JB03138.  

HypoDD:  
Waldhauser, F., and W. L. Ellsworth (2000). A double-difference earthquake location algorithm: Method and application to the northern Hayward fault, California, Bull. Seismol. Soc. Am. 90, no. 6, 1353–1368, doi: 10.1785/0120000006.  

GrowClust:  
Trugman, D. T., and P. M. Shearer (2017). GrowClust: A hierarchical clustering algorithm for relative earthquake relocation, with application
to the Spanish Springs and Sheldon, Nevada, earthquake sequences, Seismol. Res. Lett. 88, no. 2A, 379–391, doi: 10.1785/0220160188.  

Match&Locate:  
Zhang, M., and L. Wen (2015). An effective method for small event detection: Match and locate (M&L), Geophys. J. Int. 200, no. 3, 1523–1537, doi: 10.1093/gji/ggu466.
