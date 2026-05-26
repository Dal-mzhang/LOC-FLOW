# LOC-FLOW
Earthquake Location Workflow

![LOCFLOW](Data/LOC-FLOW_workflow.jpg)

LOC-FLOW is an “hands-free” earthquake location workflow to process continuous seismic records: from raw waveforms to well located earthquakes with magnitude calculations. The package assembles several popular routines for sequential earthquake location refinements, suitable for catalog building ranging from local to regional scales. DOI:10.5281/zenodo.5875084

The LOC-FLOW is released and maintained at https://github.com/Dal-mzhang/LOC-FLOW.

How to start? bash run_all.sh. 
Detailed step-by-step explanations can be found in the CookBook and corresponding scripts.

Dependent packages in LOC-FLOW include PhaseNet [contains Obspy], SeisBench, REAL, NonLinLoc, VELEST, HYPOINVERSE, hypoDD, GrowClust, FDTCC, Match&Locate; see [STEP 0 in the CookBook or src]. Questions related to the original packages should be addressed to the corresponding authors.

All other credits to Miao Zhang (also author of REAL and Match&Locate), Min Liu (also author of FDTCC), and Tian Feng, who integrated these packages and made the I/O codes publicly available. We thank Weiqiang Zhu for help with the PhaseNet. The CookBook is prepared by Ruijia Wang and Miao Zhang.

Users are free to make modifications to the programs to meet their particular needs, but are discouraged from distributing modified code to others without notification of the authors. If you find any part of the workflow useful, please cite our work or the corresponding publications of the packages.

Please download (src/software_download.py) and regularly check source code updates: PhaseNet: https://github.com/wayneweiqiang/PhaseNet; SeisBench: https://github.com/seisbench/seisbench; REAL: https://github.com/Dal-mzhang/REAL; NonLinLoc: https://github.com/ut-beg-texnet/NonLinLoc; FDTCC: https://github.com/MinLiu19/FDTCC; hypoDD: https://www.ldeo.columbia.edu/~felixw/hypoDD.html; GrowClust: https://github.com/dttrugman/GrowClust; Match&Locate: https://github.com/Dal-mzhang/MatchLocate2; HYPOINVERSE: https://www.usgs.gov/node/279394 or https://faldersons.net/Software/Hypoinverse/Hypoinverse.html

## Optional SeisBench, NonLinLoc, and SSST workflow

This branch adds optional modules for SeisBench picking, NonLinLoc absolute location, and iterative source-specific station-term (SSST) relocation. Existing LOC-FLOW picker, location, hypoDD, GrowClust, and Match&Locate steps remain available.

SeisBench picking reads the standard LOC-FLOW waveform and station layout:

```text
Data/waveform_sac/YYYYMMDD/NET.STA.CHANNEL
Data/station.dat
```

It writes REAL-compatible pick files:

```text
Pick/SeisBench/picks/<model_label>/YYYYMMDD/NET.STA.P.txt
Pick/SeisBench/picks/<model_label>/YYYYMMDD/NET.STA.S.txt
```

Each pick line remains `seconds_since_midnight probability amplitude`, matching REAL's expected format. Example:

```bash
cd Pick/SeisBench
python runseisbench.py --models PhaseNet_original --start-date 2016-10-14 --nday 1 --device auto
```

To associate SeisBench picks with REAL, pass the model label directly or use picker mode 3:

```bash
cd REAL
perl runREAL.pl PhaseNet_original
perl runREAL.pl 3 PhaseNet_original
```

NonLinLoc input preparation reads REAL association output, station metadata, and the velocity model:

```text
REAL/*.phase_sel.txt
Data/station.dat
REAL/tt_db/mymodel.nd
```

Initial NonLinLoc location:

```bash
cd NonLinLoc
bash run_nonlinloc.sh
```

Iterative SSST relocation:

```bash
cd NonLinLoc
NLL_BIN_DIR=/path/to/NonLinLoc/src/bin bash run_ssst_relocations.sh
```

The final SSST CSV is written to:

```text
NonLinLoc/out/SSST/loc_ssst_corr4/LOCFLOW.sum.grid0.loc.csv
```

NonLinLoc pick uncertainties support `fixed`, `residual`, and `auto` modes. Residual mode reads REAL `phase_sel` residuals and applies:

```text
sigma = min(max(abs(residual), phase_floor), sigma_cap)
```

The default floors are P = 0.02 s and S = 0.04 s, with a default cap of 0.50 s. `auto` uses residuals where available and falls back to fixed uncertainties otherwise.

To use these steps through `run_all.sh`, set `picker=3` and edit `seisbench_model`, `inlloc`, `issst`, and the NonLinLoc scripts for your study-specific grid, datum, velocity model, and thresholds. Set `hypo=-1` if you want to skip the traditional LOC-FLOW location/refinement steps after running NonLinLoc/SSST.

An English tutorial at https://drive.google.com/file/d/1Bka_bG55fJwXlvp8oJINgTRKqcnTrvpg/view?usp=drive_link; A Chinese tutorial at https://drive.google.com/file/d/1zlaubeYgmQnBeCO9dz627HXrtrwy79rm/view?usp=sharing (recorded video at https://www.koushare.com/video/videodetail/14767)

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

HYPOINVERSE:  
Klein, F. W. (2002). User’s guide to HYPOINVERSE-2000, a Fortran program to solve for earthquake locations and magnitudes, U.S. Geol. Surv. Open-File Rept. 2002-171, doi: 10.3133/ofr02171.  

HypoDD:  
Waldhauser, F., and W. L. Ellsworth (2000). A double-difference earthquake location algorithm: Method and application to the northern Hayward fault, California, Bull. Seismol. Soc. Am. 90, no. 6, 1353–1368, doi: 10.1785/0120000006.  

GrowClust:  
Trugman, D. T., and P. M. Shearer (2017). GrowClust: A hierarchical clustering algorithm for relative earthquake relocation, with application
to the Spanish Springs and Sheldon, Nevada, earthquake sequences, Seismol. Res. Lett. 88, no. 2A, 379–391, doi: 10.1785/0220160188.  

Match&Locate:  
Zhang, M., and L. Wen (2015). An effective method for small event detection: Match and locate (M&L), Geophys. J. Int. 200, no. 3, 1523–1537, doi: 10.1093/gji/ggu466.

# Major updates:
Dec. 24, 2023

Integrated EQTransformer and OBSTransformer into LOC-FLOW, contributed by Alireza Niksejel (the developer of OBSTransformer).

See major udpates and readme files under Data and Pick directories.

EQTransformer: https://github.com/smousavi05/EQTransformer 

Mousavi, S.M., W.L. Ellsworth, W. Zhu, L.Y. Chuang, and G.C. Beroza (2020). Earthquake transformer—an attentive deep-learning model for simultaneous earthquake detection and phase picking. Nat Commun 11, 3952, doi: 10.1038/s41467-020-17591-w

OBSTransformer: https://github.com/alirezaniki/OBSTransformer 

Niksejel, A. and M. Zhang M (2024). OBSTransformer: A Deep-Learning Seismic Phase Picker for OBS Data Using Automated Labelling and Transfer Learning. Geophys. J. Int. 237, 485–505, doi: 10.1093/gji/ggae049

May. 23, 2026

SeisBench: https://github.com/seisbench/seisbench
Woollam, J., Münchmeyer, J., Tilmann, F., Rietbrock, A., Lange, D., Bornstein, T., Diehl, T., Giunchi, C., Haslinger, F., Jozinović, D., Michelini, A., Saul, J., & Soto, H. (2022). SeisBench: A Toolbox for Machine Learning in Seismology. Seismological Research Letters, doi: 10.1785/0220210324.

NonLinLoc: https://github.com/ut-beg-texnet/NonLinLoc
Lomax, A., Virieux, J., Volant, P., and Berge-Thierry, C. (2000). Probabilistic earthquake location in 3D and layered models: Introduction of a Metropolis-Gibbs method and comparison with linear locations. In Advances in Seismic Event Location, 101-134, doi: 10.1007/978-94-015-9536-0_5.

SSST: https://github.com/ut-beg-texnet/NonLinLoc
Lomax, A., and Savvaidis, A. (2022). High-precision earthquake location using source-specific station terms and inter-event waveform similarity. Journal of Geophysical Research: Solid Earth, 127, e2021JB023190, doi: 10.1029/2021JB023190.
