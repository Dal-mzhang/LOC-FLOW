#!/usr/bin/perl
# isingle == 0: location+model updation; isingle == 1: location alone

@ARGV == 7 || die "perl $0 latref lonref distmax isingle station velmodel phasein\n";
$reflat = $ARGV[0];
$reflon = $ARGV[1];
$distmax = $ARGV[2];
$isingle = $ARGV[3];
$station = $ARGV[4];
$vel = $ARGV[5];
$phasein = $ARGV[6];
chomp($phasein);

print"isingle = $isingle\n";

if (-e "final.CNV"){`rm velest.* initial.cat final.CNV`;}

$reflon = $reflon*-1; # NOTE: western lon is positive in velest!!! e.g., 117.5W => 117.5
$iusestacorr = 1; # station correction used or not
$zmin = -0.2; # the smallest depth allowed (e.g., -0.2 -> above the sea level)
$iuseelev = 0; # station elevation used or not (recommend: 0)
$lowvelocity = 0; # any low velocity layer in the region (recommend: 0)
$vthet = 10; # damping of velocity
$stathet = 1; # damping of station correction

if($isingle == 1){
    $ittmax = 99;
    $invertratio = 0;
}else{
    $ittmax = 9;
    $invertratio = 3;
}


##############################################
# station format conversion
##############################################
$stause = "velest.sta"; #station format for VELEST
open(JK,"<$station");
@par = <JK>;
close(JK);

$p1=0;
$p2=1;
$p3=1;
$v1=0.00;
$v2=0.00;
open(OT,">$stause");
#print OT "(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)\n"; #in old code
print OT "(a6,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)\n"; #in modified code
foreach $_(@par){
	chomp($_);
	($lon,$lat,$net,$sta,$comp,$elev) = split(" ",$_);
    #if(length($sta)>4){$sta = substr($sta,1,4);}  #in old code
	$vsn = "N";$vew = "E";
	if($lat < 0.0){$vsn = "S";$vsn = -1*$vsn;}
	if($lon < 0.0){$vew = "W";$lon = -1*$lon;}
    $p1 = $elev*1000;
	printf OT "%-6s%7.4f%1s %8.4f%s %4d %1d %3d %5.2f  %5.2f\n",$sta,$lat,$vsn,$lon,$vew,$p1,$p2,$p3,$v1,$v2;
	$p3++;
}
print OT "\n";
close(OT);

################################################
# velocity model format conversion
###############################################
$newvel = "velest.mod";
open(JK,"<$vel");
@par = <JK>;
close(JK);

open(NV,">$newvel") or die "cannot write to file '$file' [$!]]\n";
# the fist title line
print NV "CALAVERAS1D-modell (mod1.1 EK280993)     Ref. station HGS\n";

for($i=0;$i<@par;$i++){
    chomp($par[$i]);
    $comp = substr($par[$i],0,6) eq "mantle";
    if($comp == 1){
        last;
    }
}
$nlayer = $i;

# the second line - indicate the number of layers for Vp
printf NV "%3d        vel,depth,vdamp,phase (f5.2,5x,f7.2,2x,f7.3,3x,a1)\n",$nlayer+2;
# add a layer above the sea level (assume the velocity wrt the sea level)
($hp,$vp,$vs,$den,$qp,$qs) = split(" ",$par[0]);
$hp = -3.0;
$vdamp = 1.0;
printf NV "%5.2f     %7.2f  %7.3f   P-VELOCITY MODEL\n",$vp,$hp,$vdamp;

# vp velocity
for($i=0;$i<$nlayer;$i++){
    chomp($par[$i]);
    ($hp,$vp,$vs,$den,$qp,$qs) = split(" ",$par[$i]);
    printf NV "%5.2f     %7.2f  %7.3f\n",$vp,$hp,$vdamp;
}
    ($hp,$vp,$vs,$den,$qp,$qs) = split(" ",$par[$i+1]);
    printf NV "%5.2f     %7.2f  %7.3f\n",$vp,$hp+0.1,$vdamp; # include the upper mantle layer

# indicate the number of layers for Vs
printf NV "%3d\n",$nlayer+2;
# add a layer above the sea level (assume the velocity wrt the sea level)
($hs,$vp,$vs,$den,$qp,$qs) = split(" ",$par[0]);
$hs = -3.0;
$vdamp = 1.0;
printf NV "%5.2f     %7.2f  %7.3f   S-VELOCITY MODEL\n",$vs,$hs,$vdamp;

# vs velocity
for($i=0;$i<$nlayer;$i++){
    chomp($par[$i]);
    ($hs,$vp,$vs,$den,$qp,$qs) = split(" ",$par[$i]);
    printf NV "%5.2f     %7.2f  %7.3f\n",$vs,$hs,$vdamp;
}
    ($hs,$vp,$vs,$den,$qp,$qs) = split(" ",$par[$i+1]);
    printf NV "%5.2f     %7.2f  %7.3f\n",$vs,$hs+0.1,$vdamp; # include the upper mantle layer
close(NV);

##################################################
#Note: VELEST doesn't have event index
#Here I use magnitude to represent its index
#The index would be used in hypoDD procedure as well
#Hope I didn't confuse you
#################################################
$phaseout = "velest.pha"; # phase format for VELEST ISED=1
$phasecat = "initial.cat"; # catalog format for VELEST

open(JK,"<$phasein");
@par = <JK>;
close(JK);

$neqs = 0;
open(EV,">$phaseout");
open(CT,">$phasecat");
foreach $file(@par){
    chomp($file);
    ($test,$jk) = split(' ',$file);
    if($test eq "#"){
		($jk,$year,$month,$day,$hour,$min,$sec,$lat,$lon,$dep,$mag,$jk,$jk,$jk,$num) = split(' ',,$file);
        $neqs++;
		$year = substr($year,2,2); # VELEST format 
		$vsn = "N";$vew = "E";
		if($lat < 0.0){$vsn = "S"; $lat = -1*$lat;} # VELEST format
		if($lon < 0.0){$vew = "W"; $lon = -1*$lon;}
		
        #$mag = $num/100; #you may want to label the event as needed
        #(3i2,1x,2i2,1x,f5.2,1x,f7.4,a1,1x,f8.4,a1,1x,f7.2,2x,f5.2)
        print EV "\n";
		printf EV "%2d%2d%2d %2d%2d %5.2f %7.4f%s %8.4f%s %7.2f  %5.2f\n",$year,$month,$day,$hour,$min,$sec,$lat,$vsn,$lon,$vew,$dep,$mag;
		printf CT "%2d%2d%2d %2d%2d %5.2f %7.4f%s %8.4f%s %7.2f  %5.2f\n",$year,$month,$day,$hour,$min,$sec,$lat,$vsn,$lon,$vew,$dep,$mag;
	}else{
        ($station,$tpick,$jk,$phase) = split(' ',$file);
		$iwt = "0";
        #if(length($station)>4){$station = substr($station,1,4);} # in old version
        #(2x,a4,2x,a1,3x,i1,3x,f6.2) # in old version
        #(2x,a6,2x,a1,3x,i1,3x,f6.2) the code was updated by M. Zhang
        printf EV "  %-6s  %-1s   %1d   %6.2f\n",$station,$phase,$iwt,$tpick;
    }
}
print EV "\n";
close(EV);
close(CT);


################################################
# velest input file preparation
################################################
$velestinput = "velest.cmn";
open(JK,">$velestinput");
print JK "velest parameters are below\n";
#***  olat       olon   icoordsystem      zshift   itrial ztrial    ised
print JK "$reflat   $reflon      0            0.0      0     0.00       1\n";
#*** neqs   nshot   rotate
print JK "$neqs      0      0.0\n";
#*** isingle   iresolcalc
print JK "$isingle      0\n";
#*** dmax    itopo    zmin     veladj    zadj   lowveloclay
print JK "$distmax   0      $zmin    0.20    5.00    $lowvelocity\n";
#*** nsp    swtfac   vpvs       nmod
print JK "2      0.75      1.730        1\n";
#***   othet   xythet    zthet    vthet   stathet
print JK "0.01    0.01      0.01    $vthet     $stathet\n";
#*** nsinv   nshcor   nshfix     iuseelev    iusestacorr
print JK  "1       0       0        $iuseelev        $iusestacorr\n";
#*** iturbo    icnvout   istaout   ismpout
print JK  "1         1         2        0\n";
#*** irayout   idrvout   ialeout   idspout   irflout   irfrout   iresout
print JK  "0         0         0         0         0         0         0\n";
#*** delmin   ittmax   invertratio
print JK  "0.001   $ittmax   $invertratio\n";
#*** Modelfile:
print JK  "$newvel\n";
#*** Stationfile:
print JK  "$stause\n";
#*** Seismofile:
print JK  " \n";                                                                               
#*** File with region names:
print JK  "regionsnamen.dat\n";
#*** File with region coordinates:
print JK  "regionskoord.dat\n";
#*** File #1 with topo data:
print JK  " \n";                                                                                
#*** File #2 with topo data:
print JK  " \n";                                                                                
#*** File with Earthquake data (phase):
print JK  "$phaseout\n";
#*** File with Shot data:
print JK  " \n";                                                                               
#*** Main print output file:
print JK "main.OUT\n";
#*** File with single event locations:
print JK "out.CHECK\n";
#*** File with final hypocenters in *.cnv format:
print JK "final.CNV\n";
#*** File with new station corrections:
print JK "sta.COR\n";
close(JK);
