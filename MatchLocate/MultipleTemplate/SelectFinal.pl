#!/usr/bin/env perl
use warnings;
#02/07/2015 initial version by Miao Zhang (ustc)
#08/22/2019 updated version by Miao Zhang (Dalhousie)
#Miao Zhang, Dalhousie University, miao.zhang@dal.ca
#
#select again based on their CC and/or N*MAD, becaulse one event might be detected by more than one template.
#merge all potential events into one file, and select one best within INTD (e.g.,6 sec) using SelectFinal.
@ARGV >= 2 || die "perl $0 Year Month Day\n";
my ($year,$month,$day) = @ARGV;
chomp($day);

my $detect = "DetectedFinal.dat";

#min number of traces
my $mintrace = "0";

#thresholds (CC/N*MAD)
my $H = "0.0/7.0";

#keep one event within 3 sec.
my $D = "3.0";

if(length($month) == 1){$month = "0$month";}
if(length($day) == 1){$day = "0$day";}

my $dir = "../$year$month$day";
my $file = "Allevents";

open(FL,">$file");
my @events = glob "$dir//*";
foreach $_(@events){
    chomp($_);
    my ($jk,$template) = split("//",$_);
    open(JK,"<$_");
    my @pars = <JK>;
    close(JK);
    my $num = @pars-1;
    shift(@pars);
    for($i=0;$i<$num;$i++){
        chomp($pars[$i]);
        my ($jk,$time,$lat,$lon,$dep,$mag,$coef,$MAD,$ntrace) = split(" ",$pars[$i]);
        if($ntrace > $mintrace){
            print FL "$time $lat $lon $dep $mag $coef $MAD $template\n";
        }   
    }
}
close(FL);

system("SelectFinal -H$H -D$D $file");

my $out = $file.".final";

open(JK,"< $out");
my @events1 = <JK>;
close(JK);

open(OUT,">$detect");
foreach $_(@events1){
    chomp($_);
    if(substr($_,0,1) eq "#"){
        print OUT "#No.      Date        Time         Lat.      Lon.        Dep.     Mag.   Coef.     N(*MAD)        Reference\n";
    }else{
        my ($num,$time,$lat,$lon,$dep,$mag,$coef,$NMAD,$ref) = split(" ",$_);
        my $hh = int($time/3600);
        my $min = int(($time-$hh*3600)/60);
        my $sec = $time - $hh*3600 - $min*60;
        printf OUT "%4d   %04d/%02d/%02d   %02d:%02d:%06.3f   %7.4f   %8.4f   %6.2f   %5.2f  %6.4f  %8.4f      %s\n",$num,$year,$month,$day,$hh,$min,$sec,$lat,$lon,$dep,$mag,$coef,$NMAD,$ref;
    }
}
unlink $out;
unlink $file;
