#!/user/bin/perl -w
@ARGV == 4 || die "$0 phasein event phaseout useall\n";
$phasein = $ARGV[0];
$event = $ARGV[1];
$phaseout = $ARGV[2];
$useall = $ARGV[3];

printf STDERR "locations in hypoDD.pha are updating\n";
open(JK,"<$phasein");
@par = <JK>;
close(JK);

open(EV,"<$event");
@eves = <EV>;
close(EV);

$out = 0;
open(EV,">$phaseout");
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
            #combine original picks &  improved locations
            if($num == $num1){
                print EV "# $year $month $day $hour $min $sec $lat1 $lon1 $dep1 $mag 0 0 $rms $num\n";
                $out = 1;
            }

        }
        if($out == 0 && $useall == 1){
            # still keep those events, which were not located by hypoDD_dtct
            # you may not have to use them if you only focus on best events from hypoDD_dtct
            print EV "# $year $month $day $hour $min $sec $lat $lon $dep $mag 0 0 $rms $num\n"; 
            $out = 1;
         }   
    }else{
        if($out>0){
            printf EV "$file\n";
        }   
    }   
}
close(EV);
