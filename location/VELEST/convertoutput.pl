#!/usr/bin/perl
use Scalar::Util qw(looks_like_number);
#
# Author: Miao Zhang, miao.zhang@dal.ca
#
@ARGV == 4 || die "perl $0 stationgap residual finalcatalog deletedcatalog\n";
$gapmax = $ARGV[0];
$resmax = $ARGV[1];
$relo = $ARGV[2];
$dele = $ARGV[3];
chomp($dele);

$relocate = "final.CNV"; # output by VELEST
if (-e $relo){`rm $relo $dele`;}

open(JK,"<$relocate");
@par = <JK>;
close(JK);

$i=0;
open(OT,">$relo");
open(DE,">$dele");
foreach $_(@par){
	chomp($_);
	if(looks_like_number(substr($_,0,2))){
	$year = substr($_,0,2);
    $mon = substr($_,2,2); $mon=~s/^\s+//;
    $day = substr($_,4,2); $day=~s/^\s+//;
    if(length($mon) == 1){$mon = "0$mon";}
    if(length($day) == 1){$day = "0$day";}

    $date = "$year$mon$day";
	$hour = substr($_,7,2);
	$min = substr($_,9,2);
	$sec = substr($_,12,5);
	$lat = substr($_,18,7);
	$lon = substr($_,27,8);
	$dep = substr($_,37,6);
	$mag = substr($_,44,10);
	$az = substr($_,54,3);
	$res = substr($_,62,5);
    if(substr($_,25,1) eq 'S'){$lat = -1*$lat;}
    if(substr($_,35,1) eq 'W'){$lon = -1*$lon;}
    #    if($dep < 0){$dep = 0.0;}
	if($az <= $gapmax && $res <= $resmax){
        $i++;
		print OT "$date $hour $min $sec $lat $lon $dep $mag $az $res $i\n";
	}else{
		print DE "$date $hour $min $sec $lat $lon $dep $mag $az $res $i\n";
	}
	}
}
close(OT);
close(DE);
