#!/usr/bin/perl
$phasein = "../../MultipleTemplate/DetectedFinal.dat"; #event catalog from MatchLocate
$phaseout = "hypoDD.pha"; #note that we don't have any picks here, we will calculate dt.cc based on P and S theorical traveltime.
$stationin = "../../../Data/station.dat"; #station list
$stationout = "stlist.txt"; #station list for growclust
$eventout = "evlist.txt"; #events for growclust 
$velin = "../../../REAL/tt_db/mymodel.nd"; #velocity model
$velout = "vzmodel.txt"; #velocity model for growclust
$waveform = "../../Template"; #template waveform directory

################################################
# station format conversion
###############################################
printf STDERR "Step 1: station format conversion\n";
open(JK,"<$stationin");
@par = <JK>;
close(JK);

open(NS,">$stationout");
foreach $_(@par){
    chomp(@par);
    ($lon,$lat,$net,$sta,$comp,$elev) = split(" ");
    print NS "$sta $lat $lon\n";
}
close(NS);

################################################
# velocity model format conversion
###############################################
printf STDERR "Step 2: velocity model format conversion\n";
open(JK,"<$velin");
@par = <JK>;
close(JK);

open(NV,">$velout");
for($i=0;$i<@par;$i++){
    chomp($par[$i]);
    $comp = substr($par[$i],0,6) eq "mantle";
    if($comp == 1){
        last;
    }
}
$nlayer = $i;
for($i=0;$i<$nlayer;$i++){
    chomp($par[$i]);
    ($hp,$vp,$vs,$den,$qp,$qs) = split(" ",$par[$i]);
    printf NV "%7.2f     %5.2f  %5.2f\n",$hp,$vp,$vs;
}
    ($hp,$vp,$vs,$den,$qp,$qs) = split(" ",$par[$i+1]);
    printf NV "%7.2f     %5.2f  %5.2f\n",$hp+0.1,$vp,$vs; #include the upper mantle layer
close(NV);

#####################
#  create hypoDD.pha
# (but without picks)
#####################   
printf STDERR "Step 3: create hypoDD.pha (without picks)\n";
open(JK,"<$phasein");
@par = <JK>;
close(JK);
#1   2016/10/14   00:00:09.150   42.8115    13.2125     5.55    0.00  0.9891   39.9168      20161014000009.15
shift(@par);
open(HP,">$phaseout");
open(EP,">$eventout");
foreach $_(@par){
     chomp($_);
     print"$_\n";
    ($num,$date,$time,$lat,$lon,$dep,$mag,$cc,$nad,$template) = split(" ",$_);
    ($year,$mon,$day) = split("/",$date);
    ($hh,$mm,$ss) = split(":",$time);
    print HP "# $year $mon $day $hh $mm $ss $lat $lon $dep $mag 0 0 0 $num\n";
    @sac = glob "$waveform/$template/*.??Z";
    foreach $sta(@sac){
        chomp($sta);
        ($jk,$kstnm,$t1,$t2) = split(" ",`saclst KSTNM t1 t2 f $sta`);
        print HP "$kstnm $t1 1 P\n";
        print HP "$kstnm $t2 1 S\n";
    }
    print EP "$year $mon $day $hh $mm $ss $lat $lon $dep $mag 0 0 0 $num\n";
}
close(HP);
close(EP);
#####################
#     make dt.ct
#####################
printf STDERR "Step 4: make dt.ct\n";
system("ph2dt ph2dt.inp");
#####################
#     make dt.cc
#####################
printf STDERR "Step 5: make dt.cc\n";
#-----------------------------Parameters setting-----------------------------
#waveform window length before and after trigger and shifting window
$W = "1.0/1.0/0.2/1.0/1.0/0.3";
#samping rate of waveform/threshold of output picks(default: 0.01/0.0)
$D = "0.01/0.6/1/1"; #optional
#ranges and grids for traveltime table in horizontal direction and  depth
$G = "1.4/20/0.01/1";
#specified path of event.sel and dt.ct (optional)
$C = "1/1/1"; 	#(0: default 1:user specify)
#data format (0: continuous data; 1: event segments)
$F = "0";
#fitering
$B = "2/8";

$staDir="../../../Data/station.dat";
$tttDir="../../../REAL/tt_db/ttdb.txt";
$wavDir="../../../Data/waveform_sac";
$eveDir="./event.sel";
$dctDir="./dt.ct";
$paDir="hypoDD.pha";

system("FDTCC -F$F -C$C -W$W -D$D -G$G -B$B $staDir $tttDir $wavDir $eveDir $dctDir $paDir");
printf STDERR "FDTCC -F$F -C$C -W$W -D$D -G$G -B$B $staDir $tttDir $wavDir $eveDir $dctDir $paDir\n";
system("rm Input.*");
