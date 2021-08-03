#!/usr/bin/perl -w
@ARGV == 1 || die "perl $0 STALTA:0 PhaseNet:1\n";
$picker=$ARGV[0];
chomp($picker);

#how to evaluate your parameters:
#1. check P and S t_dist curve (if too narrow, increase nrt; vice versa)
#2. make sure you lose very few events after the second selection (if lose too many, 
#   increase thresholds, e.g.,increase np0, ns0, nps0 and/or npsboth0)
#3. go to event_verify and check those worst events (least number of picks, 
#   large station gap and traveltime residual) and make sure they are ture events,
#   otherwise, increase your thresholds.
#4. go to the ../location/hypoinverse dir, run hypoinverse, unstable events usually 
#   show REMARK "-", use their ID to check their waveform in event_verify.
#   if they are false events, increase your thresholds.

#tips:
#1. decrease drt (< 1.0, 0 is the best) will improve the stability but will cost more time, 
#   0 means no nearby initiating picks will be removed. It is time afforable 
#   (a couple of minutes) if your total number of grids is only about 1000 (i.e.,10x10x10).
#2. nrt and grid size (tdx and tdh) trade off, when you use small grid size, choose a large 
#   nrt (but may < 2.0). When you use large grid size, please use a small nrt and decrease the drt.
#3. nxd and rsel can be used to remove those suspicious events and picks, respectively.
#4. you may get less events when you use loose thresholds compared to strict ones when the drt > 0.
#5. the main purpose is assocaition, don't have to refine the grid to have a better location.
#6. more picks or stations, more strict thresholds. Compared to machine-learing picks, STALTA picks 
#   require more strict thresholds.
#7. common problems: too slow -> the total number of girds is too big
#                    false events -> too loose thresholds
#                    bad performance -> didn't use optimal parameters for different grid size


#startting date and number of days
$year0 = "2016";
$month0 = "10";
$day0 = "14";
$nday = "1";

$ID=0;
$phaseSAall = "phaseSA_allday.txt";
open(OUT,">$phaseSAall");

for($i=0; $i<$nday; $i++){
	if($i == 0){
	$year = $year0; $month=$month0; $day = $day0;
	}else{
	($year,$month,$day) = &Timeadd($year0,$month0,$day0,1);}
	$year0 = $year; $month0 = $month; $day0 = $day;
	print"$year $month $day\n";
	if(length($month)==1){$month = "0".$month;} 
	if(length($day)==1){$day = "0".$day;} 
	$outfile ="$year$month$day";

    # -D(nyear/nmon/nday/lat_center)
    $D = "$year/$month/$day/42.75";
    # -R(rx/rh/tdx/tdh/tint[/gap/GCarc0/latref0/lonref0]])
    #$R = "0.1/20/0.02/2/5"; # small gride size
    $R = "0.1/20/0.04/2/5"; # large grid size
    # -G(trx/trh/tdx/tdh)
    $G = "1.4/20/0.01/1";
    # -V(vp0/vs0/[s_vp0/s_vs0/ielev])
    $V = "6.2/3.4";
    # -S(np0/ns0/nps0/npsboth0/std0/dtps/nrt/[drt/nxd/rsel/ires])
    #$S = "3/2/8/2/0.5/0.1/1.8/0.35"; # for small grid size
    $S = "3/2/8/2/0.5/0.1/1.2/0.0"; # for large grid size
    
    # thresholds may change with pickers, here for rough testing
    if ($picker==0){
        $dir = "../Pick/STALTA/$year$month$day"; # use STA/LTA picks
    }elsif($picker==1){
        $dir = "../Pick/PhaseNet/$year$month$day"; # use PhaseNet picks
    }else{
        printf STDERR "please choose 0: STALTA or 1: PhaseNet";
    }
    $station = "../Data/station.dat";
    $ttime = "./tt_db/ttdb.txt";

    system("REAL -D$D -R$R -S$S -G$G -V$V $station $dir $ttime");
    print"REAL -D$D -R$R -S$S -G$G -V$V $station $dir $ttime\n";
    `mv catalog_sel.txt $outfile.catalog_sel.txt`;
    `mv phase_sel.txt $outfile.phase_sel.txt`;
    `mv hypolocSA.dat $outfile.hypolocSA.dat`;
    `mv hypophase.dat $outfile.hypophase.dat`;

    $hypophase_file = $outfile.".hypophase.dat";
    open(EV,"<$hypophase_file");
    @par = <EV>;
    close(EV);

    foreach $_(@par){
	    chomp($_);
            $beigin = substr($_,0,1);
            if($beigin eq "#"){
            ($jk,$year,$month,$day,$hour,$min,$sec,$evla,$evlo,$evdp,$evmg,$EH,$EZ,$RMS,$nn) = split(" ",$_);chomp($nn);
            $nn=$nn+$ID;
            printf OUT "%1s %04d %02d %02d %02d %02d %06.3f  %8.4f  %9.4f  %6.3f %5.2f %7.2f %7.2f %7.2f      %06d\n",$jk,$year,$month,$day,$hour,$min,$sec,$evla,$evlo,$evdp,$evmg,$EH,$EZ,$RMS,$nn;
            }else{print OUT "$_\n";}	
    }
    $ID=$nn;
}
close(OUT);

#events with large number of picks and small station gap
#can be used for velocity model updation in VELEST
$numps = 30; # minimum number of P and S picks
$gap = 180; # largest station gap

$phaseall = "phase_allday.txt";
$catalogall = "catalog_allday.txt";
$catalogSAall = "catalogSA_allday.txt";
$phasebest = "phase_best_allday.txt";

`cat *.phase_sel.txt > $phaseall`;
`cat *.catalog_sel.txt > $catalogall`;
`cat *.hypolocSA.dat > $catalogSAall`;

&PhaseBest($phaseall,$phasebest,$numps,$gap); # maybe used for velocity model updating in VELEST
&PhaseAll($phaseall); # will be used in VELEST 

sub PhaseAll{
    my($file) = @_;
	open(JK,"<$file");  
	@par = <JK>;
	close(JK);
    
    $num = 0;
    open(OT,">$file");
	foreach $file(@par){
        chomp($file);
		($test,$jk) = split(' ',$file);
		if($test =~ /^\d+$/){
			($jk,$year,$mon,$dd,$time,$ot,$std,$lat,$lon,$dep,$mag,$jk,$nofp,$nofs,$nofps,$nboth,$gap) = split(' ',,$file);
			($hour,$min,$sec) = split('\:',$time);
			$num++;
			print OT "# $year  $mon  $dd   $hour    $min    $sec    $lat    $lon    $dep     $mag     0.0     0.0    0.0    $num\n";
		}else{
			($net,$station,$phase,$traveltime,$pick,$amplitude,$res,$prob,$baz) = split(' ',$file);
			print OT "$station $pick $prob $phase\n";
		}
	}
    close(OT);
}

sub PhaseBest{
    my($filein,$fileout,$numps,$gap0) = @_;
	open(JK,"<$filein");  
	@par = <JK>;
	close(JK);
    
    $num = 0;
    open(OT,">$fileout");
	foreach $file(@par){
		($test,$jk) = split(' ',$file);
        if($test =~ /^\d+$/){
            ($jk,$year,$mon,$dd,$time,$ot,$std,$lat,$lon,$dep,$mag,$jk,$nofp,$nofs,$nofps,$nboth,$gap) = split(' ',,$file);
            ($hour,$min,$sec) = split('\:',$time);
            $iok = 0;
            if($nofps >= $numps && $gap <= $gap0){
			    $num++;
			    print OT "# $year  $mon  $dd   $hour    $min    $sec    $lat    $lon    $dep     $mag     0.0     0.0    0.0   $num\n";
                $iok = 1;
            }
         }else{
             if($iok == 1){
            ($net,$station,$phase,$traveltime,$pick,$amplitude,$res,$prob,$baz) = split(' ',$file);
            print OT "$station $pick $prob $phase\n";
            }
		}
	}
    close(OT);
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
