#!/usr/bin/env perl
use warnings;
#######################################
#       A perl script to call Match&Locate for detecting and locating low-magnitude events
#       Miao Zhang  11/22/2013  USTC        inital version
#       Miao Zhang  02/07/2015  USTC        add description (M&L1)
#       Miao Zhang  08/22/2019  Dalhousie   change inputs (M&L2)
#       Miao Zhang  07/2021     Dalhousie   add the -B option
# Reference: Zhang and Wen, GJI, 2015
# Email: miao.zhang@dal.ca
#######################################
#Make sure the begin and end time of all the continuous seismograms are equal.
@ARGV >= 2 || die "perl $0 dir1(reference event) dir2(continuous data) INPUT F\n";
$dir1 = $ARGV[0];
$dir2 = $ARGV[1];
$inputfile = $ARGV[2];

#Selcet suitable phases (single phase or multiple phases)
#multiphase == 0 (use only phase, $phase0)
#multiphase == 1 use multiple phases, just ignore parameter $phase0 (larger distance)
$multphase = "0";
$phase0 = "S";

#Search center
#Refevla/refevlo/refevdp
#Usually, centered at the template location.
$F = $ARGV[3];
chomp($F);

#Search area
#MaxLat/MaxLon/MaxDepth
#"0/0/0" corresponds to matched-filter case.
#If you don't want to search depth, please fix depth to be zero.
#There would be a strong trade-off between origin time and depth if the station coverage is not very well.
#$R = "0.05/0.05/0";
$R = "0.0/0.0/0";

#Search inveral
#Dlat/Dlon/Ddepth (must not be zero for any one!)
$I = "0.01/0.01/0.5";

#output stacked cross-correlograms
#0 ----> don't output
#1 ----> just output the stacked cross-correlogram for the optimal location.[default]
#2 ----> just output the stacked cross-correlogram for each searching grid.
#3 ----> output the CC distribution at each searching grid (for plotting CC).
$O = "0";

#Time interval
#Keep one event within a certain time window (e.g., 6 sec).
#It depends on your search area and station distance.
$D = "3.0";

##WindowLength/before/after
##The cross-correlation window based on the marked t1 in your templates.
#Here 4 sec is used, 1 sec before and 3 sec after the marked t1.
$T = "2.0/0.5/1.5";

#Detection thresholds
#One event is detected when 1) CC >= THRESH && 2) NMAD(*MAD) >= N(*MAD)
#You may use CC (e.g., 0.3/0.0) and MAD (e.g., 0.0/10.0) individually or simultaneously (e.g., 0.3/10.0)
$H = "0.0/7.0";

###fitering range low/high
#-1/-1 will not fiter
$B = "2/8";

#station parameter
#1.Channel number
#2.Template_dir Trace_dir dt_dD(horizontal slowness)/dt_dh(vertical slowness)
#3. ...
$INPUT = "INPUT.in";

#create input file for M&L
$markornot = 1;

#show warnnings if on enough components/stations
#assume 3 components for each stations
#locations cannot be well-constrained if less than 3 stations
my $stablenum = 9;

$TB = time();

if($markornot == 1){
open(ST,"<$inputfile");
@sta = <ST>;
close(ST);
if(-e $INPUT){`rm $INPUT`;}
open(AA,">$INPUT");

if(@sta < $stablenum){
        printf STDERR "Warnning: you don't have enough components/stations!\n";
        printf STDERR "          Locations may be not constrained well!\n";
}

for($i=0;$i<@sta;$i++){
    my ($station,$t1,$DT,$ttmark,$phase) = split(" ",$sta[$i]);
    $station = sprintf("%-s",$station);
    #Make sure common stations are in both directories.
    if(-e "$dir1/$station" && -e "$dir2/$station"){
	    if($multphase == 1){
        	print AA "$dir1/$station $dir2/$station $DT $ttmark $phase\n";
	    }elsif($multphase == 0 && $phase eq $phase0){
        	print AA "$dir1/$station $dir2/$station $DT $ttmark $phase\n";
    	    }
    }
}
close(AA);



open(AA,"<$INPUT");
@par = <AA>;
close(AA);
$num = @par;

open(NEW,">$INPUT");
print NEW "$num\n";
for($i=0; $i<@par;$i++){
    chomp($par[$i]);
    print NEW "$par[$i]\n";
}
close(NEW);
}

($maxlat,$maxlon,$maxh) = split('/',$R);
($dlat,$dlon,$dh) = split('/',$I);
$np = int(2*$maxlat/$dlat + 1)*(int(2*$maxlon/$dlon + 1))*int((2*$maxh/$dh + 1));
print STDERR "There are $np potential locations\n";
system("MatchLocate2 -F$F -R$R -I$I -T$T -H$H -D$D -B$B -O$O $INPUT");
printf STDERR "MatchLocate2 -F$F -R$R -I$I -T$T -H$H -D$D -B$B -O$O $INPUT\n";

if($O == 1 ){
    $stackcc1 = "SELECT_STACKCC";
    if(-e $stackcc1){`rm $stackcc1/*`;}
    else{`mkdir $stackcc1`}
    `mv *.stack $stackcc1/`;
}

$TE = time();
$time = $TE - $TB;
printf STDERR "Time consuming is %6.2f mins\n",$time/60.0;
