#!/usr/bin/perl
$phasein = "../../hypoDD_dtct/hypoDD.pha"; #phase file
$event = "../../hypoDD_dtct/hypoDD.reloc"; #events for hypoDD 
$phaseout = "hypoDD.pha"; #updated phase file using hypoDD relocations
$stationin = "../../Data/station.dat"; #station list
$stationout = "stlist.txt"; #station list for growclust
$eventout = "evlist.txt"; #events for growclust 
$velin = "../../REAL/tt_db/mymodel.nd"; #velocity model
$velout = "vzmodel.txt"; #velocity model for growclust
$maxdep = 20; #maximum depth in the traveltime table
$useall = 1;  #0: only use available events from hypoDD.reloc (dt.ct)
              #1: use all events, only update locations from hypoDD.reloc (dt.ct)

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
    printf NV "%7.2f     %5.2f  0.0\n",$hp,$vp;
}
close(NV);

################################################
# Phase file update
###############################################
printf STDERR "Step 3: update phase file\n";
open(JK,"<$phasein");
@par = <JK>;
close(JK);

open(EV,"<$event");
@eves = <EV>;
close(EV);

open(EV,">$phaseout");
open(EV1,">$eventout");
foreach $file(@par){
    chomp($file);
    ($test,$jk) = split(' ',$file);
    if($test eq "#"){
		($jk,$year,$month,$day,$hour,$min,$sec,$lat,$lon,$dep,$mag,$jk,$jk,$rms,$num) = split(' ',,$file);
		$out = 0;
		foreach $eve(@eves){
			chomp($eve);
			($num1,$lat1,$lon1,$dep1,$jk,$jk,$jk,$jk,$jk,$jk,$year1,$day1,$month1,$day1,$hh1,$mm1,$ss1,$jk,$jk,$jk,$jk,$jk,$jk,$jk,$jk) = split(" ",$eve);
            #if($dep1 < 0.1){$dep1 = 0.1;} 
            if($dep1 > $maxdep){next;} 
            #combine original picks &  improved locations
			if($num == $num1){
				print EV "# $year $month $day $hour $min $sec $lat1 $lon1 $dep1 $mag 0 0 $rms $num\n";
				print EV1 "$year $month $day $hour $min $sec $lat1 $lon1 $dep1 $mag 0 0 $rms $num\n";
				$out = 1;
			}
		}
        if($out == 0 && $useall == 1){
                print EV "# $year $month $day $hour $min $sec $lat $lon $dep $mag 0 0 $rms $num\n";
                print EV1 "$year $month $day $hour $min $sec $lat $lon $dep $mag 0 0 $rms $num\n";
                $out = 1;
        }
	}else{
		if($out>0){
			printf EV "$file\n";
		}
    }
}
close(EV);
close(EV1);
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
$W = "1.0/1.0/0.3/1.0/1.5/0.5";
#samping rate of waveform/threshold of output picks(default: 0.01/0.0)
$D = "0.01/0.6/1/2"; #optional
#ranges and grids for traveltime table in horizontal direction and  depth
$G = "1.4/20/0.01/1";
#specified path of event.sel and dt.ct (optional)
$C = "1/1/1"; 	#(0: default 1:user specify)
#data format (0: continuous data; 1: event segments)
$F = "0";
#fitering
$B = "2/8";

$staDir="../../Data/station.dat";
$tttDir="../../REAL/tt_db/ttdb.txt";
$wavDir="../../Data/waveform_sac";
$eveDir="./event.sel";
$dctDir="./dt.ct";
$paDir="./hypoDD.pha";

system("FDTCC -C$C -F$F -W$W -D$D -G$G -B$B $staDir $tttDir $wavDir $eveDir $dctDir $paDir");
printf STDERR "FDTCC -C$C -F$F -W$W -D$D -G$G -B$B $staDir $tttDir $wavDir $eveDir $dctDir $paDir\n";
system("rm Input.*");
