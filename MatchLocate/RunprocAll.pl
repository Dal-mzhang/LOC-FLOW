#!/usr/bin/env perl
use warnings;
# Author: Miao Zhang    02/07 2015
#         Miao Zhang    08/26 2019
# Reference: Zhang and Wen, GJI, 2015
# Email: zhmiao@mail.ustc.edu.cn
# Event Format:
#  Date        Time        Lat.      Lon.     Dep.  M  Mag. 
#2012/09/02  03:00:45.74  37.799   139.998   7.8    M  2.1
# All the template files should be named by their origin times. (e.g., 20120902030045.74)
# The slave continuous data should be named by its date. (e.g., 20120902)
@ARGV == 1 || die"perl $0 event\n";
$event = $ARGV[0];
chomp($event);

open(EV,"<$event");
@par = <EV>;
close(EV);

#Template directory
$dir1 = "./Template";
#Slave continuous data directory
$dir2 = "../Data/waveform_sac/";

#Beginning date
$year0 = "2016";
$month0 = "10";
$day0 = "14";

#Day length
$dleng = "1"; 

for($i=0;$i<$dleng;$i++){
	if($i == 0){
	$year = $year0; $month=$month0; $day = $day0;
	}else{
	($year,$month,$day) = &Timeadd($year0,$month0,$day0,1);}
	
	$year0 = $year; $month0 = $month; $day0 = $day;
	print"$year $month $day\n";
	if(length($month)==1){$month = "0".$month;} 
	if(length($day)==1){$day = "0".$day;} 
	$outfile ="$year$month$day";
	if(!-e $outfile){system"mkdir $outfile";}
foreach $_(@par){
	chomp($_);
	($date,$time,$evla,$evlo,$evdp,$jk,$evmg) = split(" ",$_);
	($ev_year,$ev_month,$ev_day) = split("/",$date);
	($ev_hour,$ev_min,$ev_sec) = split(":",$time);

	$name = "$ev_year"."$ev_month"."$ev_day"."$ev_hour"."$ev_min"."$ev_sec";
	$F = "$evla/$evlo/$evdp"; #you can modify the referece point. Default is the template location.
	print"$name $year/$month/$day\n";
	system("perl PROC_MatchLocate.pl $dir1/$name $dir2/$year$month$day $dir1/INPUT/$name $F");
	system("mv EventCase.out $outfile/$name");
}
}

sub Timeadd{
   my($yyear,$mm,$dday,$adday) = @_;
   $dday = $dday + $adday;	
   if (($mm==1) || ($mm==3) || ($mm==5) || ($mm==7) || ($mm==8) || ($mm==10) || ($mm==12)){
      if ($dday >31) {
         $dday = 1;
         $mm = $mm + 1;
         if ($mm > 12) {
            $mm = 1;
            $yyear = $yyear + 1;
         }
      }
   }    
   if (($mm==4) || ($mm==6) || ($mm==9) || ($mm==11)){
      if ($dday >30) {
         $dday = 1;
         $mm = $mm + 1;
         if ($mm > 12) {
            $mm = 1;
            $yyear = $yyear + 1;
         }
      }
   }    
   if ($mm == 2) {
      if ((($yyear%4 == 0) && ($yyear%100 != 0)) || ($yyear%400 == 0)){
         if ($dday >29) {
            $dday = 1;
            $mm = $mm + 1;
         }
      }
      else{
        if ($dday >28) {
            $dday = 1;
            $mm = $mm + 1;
         }
      }
   }

   my @time = ($yyear,$mm,$dday);
   return(@time);
}
