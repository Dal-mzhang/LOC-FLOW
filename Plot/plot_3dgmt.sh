#!/usr/bin/env -S bash -e
gmt set PS_PAGE_ORIENTATION Portrait PS_MEDIA 9ix10.5i
gmt set FONT_TAG 20p FONT_HEADING 25p MAP_HEADING_OFFSET 0p FONT_LABEL 20p FONT_ANNOT 16p
export GMT_SESSION_NAME=$$	# Set a unique session name

# 1-output figure; 0-don’t output.
#fig_format=jpg,pdf
fig_format=jpg

# initial locations
#REAL simulated annealing locations (hypo=0)
REAL_SA=0
loc11=../REAL/catalogSA_allday.txt
#VELEST locations                   (hypo=1)
VELEST=0
loc12=../location/VELEST/new.cat
#hypoinverse locations              (hypo=2 or 3)
hypoinverse=1
loc13=../location/hypoinverse/new.cat      #2
#loc13=../location/hypoinverse_corr/new.cat #3

# hypoDD CT locations
hypoDD_CT=1
loc2=../hypoDD_dtct/hypoDD.reloc
# hypoDD CC locations
hypoDD_CC=1
loc3=../hypoDD_dtcc/hypoDD.reloc
# Growclust locations
Growclust=1
loc4=../GrowClust/OUT/out.growclust_cat

# study region
lon1=12.9
lon2=13.4
lat1=42.4
lat2=43
dep1=0
dep2=20

# you may only show those events with min number of double-difference P pairs in hypoDD and growclust catalogs
# also consider useall=0 in hypoDD_dtcc/run_hypoDD_dtcc.sh and GrowClust/IN/gen_input.pl
nddp=0;
#nddp=5;

lon_range=5 # lon_range=5i
lat_range=$(printf "%.3f" `echo "scale=4;($lat2-$lat1)*$lon_range/($lon2-$lon1)"|bc`)
dep_range=$(printf "%.3f" `echo "scale=4;($dep2-$dep1)*$lon_range/(($lon2-$lon1)*111.19)"|bc`)

lon_range=`echo $lon_range|awk '{print $1"i"}'`  # lon_range=5i
lat_range=`echo $lat_range|awk '{print $1"i"}'`  # lat_range=6i
dep_range=`echo $dep_range|awk '{print $1"i"}'`  # dep_range=1.799i


############################################## plot for REAL SA catalog
if [ $REAL_SA == 1 ]
then
gmt begin REAL_SA $fig_format
gmt subplot begin 2x2 -Fs$lon_range,$dep_range/$lat_range,$dep_range -A -M0.2c/0.1c -T"REAL_SA catalog"

gmt subplot set 0,0
projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa0.1 -Bya0.1+l"Latitude (deg.)" -BWSen
cat $loc11|gawk  '{print $8, $7}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 0,1
projection="X$dep_range/$lat_range"
region="$dep1/$dep2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa5+l"Depth (km)" -Bya0.1 -BWSen
cat $loc11|gawk  '{print $9, $7}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 1,0
projection="X$lon_range/-$dep_range"
region="$lon1/$lon2/$dep1/$dep2"
gmt basemap -R$region -J$projection  -Bxa0.1+l"Longitude (deg.)" -Bya5+l"Depth (km)" -BWSen
cat $loc11|gawk  '{print $8, $9}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot end
gmt end show
fi
##############################################

############################################## plot for VELEST catalog
if [ $VELEST == 1 ]
then
gmt begin VELEST $fig_format
gmt subplot begin 2x2 -Fs$lon_range,$dep_range/$lat_range,$dep_range -A -M0.2c/0.1c -T"VELEST catalog"

gmt subplot set 0,0
projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa0.1 -Bya0.1+l"Latitude (deg.)" -BWSen
cat $loc12|gawk  '{print $6, $5}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 0,1
projection="X$dep_range/$lat_range"
region="$dep1/$dep2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa5+l"Depth (km)" -Bya0.1 -BWSen
cat $loc12|gawk  '{print $7, $5}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 1,0
projection="X$lon_range/-$dep_range"
region="$lon1/$lon2/$dep1/$dep2"
gmt basemap -R$region -J$projection  -Bxa0.1+l"Longitude (deg.)" -Bya5+l"Depth (km)" -BWSen
cat $loc12|gawk  '{print $6, $7}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot end
gmt end show
fi
##############################################

############################################## plot for hypoinverse catalog
if [ $hypoinverse == 1 ]
then
gmt begin hypoinverse $fig_format
gmt subplot begin 2x2 -Fs$lon_range,$dep_range/$lat_range,$dep_range -A -M0.2c/0.1c -T"HYPOINVERSE catalog"

gmt subplot set 0,0
projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa0.1 -Bya0.1+l"Latitude (deg.)" -BWSen
cat $loc13|gawk  '{print $6, $5}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 0,1
projection="X$dep_range/$lat_range"
region="$dep1/$dep2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa5+l"Depth (km)" -Bya0.1 -BWSen
cat $loc13|gawk  '{print $7, $5}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 1,0
projection="X$lon_range/-$dep_range"
region="$lon1/$lon2/$dep1/$dep2"
gmt basemap -R$region -J$projection  -Bxa0.1+l"Longitude (deg.)" -Bya5+l"Depth (km)" -BWSen
cat $loc13|gawk  '{print $6, $7}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot end
gmt end show
fi
##############################################

############################################## plot for hypoDD_CT catalog
if [ $hypoDD_CT == 1 ]
then
gmt begin hypoDD_CT $fig_format
gmt subplot begin 2x2 -Fs$lon_range,$dep_range/$lat_range,$dep_range -A -M0.2c/0.1c -T"hypoDD catalog (dt.ct)"

gmt subplot set 0,0
projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa0.1 -Bya0.1+l"Latitude (deg.)" -BWSen
cat $loc2|gawk  '{if($20 >= '''$nddp''') print $3, $2}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 0,1
projection="X$dep_range/$lat_range"
region="$dep1/$dep2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa5+l"Depth (km)" -Bya0.1 -BWSen
cat $loc2|gawk  '{if($20 >= '''$nddp''') print $4, $2}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 1,0
projection="X$lon_range/-$dep_range"
region="$lon1/$lon2/$dep1/$dep2"
gmt basemap -R$region -J$projection  -Bxa0.1+l"Longitude (deg.)" -Bya5+l"Depth (km)" -BWSen
cat $loc2|gawk '{if ($20 >= '''$nddp''') print $3, $4}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot end
gmt end show
fi
##############################################

############################################## plot for hypoDD_CC catalog
if [ $hypoDD_CC == 1 ]
then
gmt begin hypoDD_CC $fig_format
gmt subplot begin 2x2 -Fs$lon_range,$dep_range/$lat_range,$dep_range -A -M0.2c/0.1c -T"hypoDD catalog (dt.cc)"

gmt subplot set 0,0
projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa0.1 -Bya0.1+l"Latitude (deg.)" -BWSen
cat $loc3|gawk  '{if($18 >= '''$nddp''') print $3, $2}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 0,1
projection="X$dep_range/$lat_range"
region="$dep1/$dep2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa5+l"Depth (km)" -Bya0.1 -BWSen
cat $loc3|gawk  '{if($18 >= '''$nddp''') print $4, $2}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 1,0
projection="X$lon_range/-$dep_range"
region="$lon1/$lon2/$dep1/$dep2"
gmt basemap -R$region -J$projection  -Bxa0.1+l"Longitude (deg.)" -Bya5+l"Depth (km)" -BWSen
cat $loc3|gawk  '{if($18 >= '''$nddp''') print $3, $4}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot end
gmt end show
fi
##############################################

############################################## plot for Growclust catalog
if [ $Growclust == 1 ]
then
gmt begin GrowClust $fig_format
gmt subplot begin 2x2 -Fs$lon_range,$dep_range/$lat_range,$dep_range -A -M0.2c/0.1c -T"GrowClust catalog"

gmt subplot set 0,0
projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa0.1 -Bya0.1+l"Latitude (deg.)" -BWSen
cat $loc4|gawk  '{if($16 >= '''$nddp''') print $9, $8}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 0,1
projection="X$dep_range/$lat_range"
region="$dep1/$dep2/$lat1/$lat2"
gmt basemap -R$region -J$projection  -Bxa5+l"Depth (km)" -Bya0.1 -BWSen
cat $loc4|gawk '{if($16 >= '''$nddp''') print $10, $8}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot set 1,0
projection="X$lon_range/-$dep_range"
region="$lon1/$lon2/$dep1/$dep2"
gmt basemap -R$region -J$projection  -Bxa0.1+l"Longitude (deg.)" -Bya5+l"Depth (km)" -BWSen
cat $loc4|gawk '{if($16 >= '''$nddp''') print $9, $10}'| gmt plot -Sc0.3c -W0.5p,black -Gred

gmt subplot end
gmt end show
fi
##############################################
rm gmt.conf
