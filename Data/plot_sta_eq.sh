#!/usr/bin/env -S bash -e
# GMT modern mode bash template
# Date:    2021-03-25T18:02:26
# User:    fengtian
# Purpose: Purpose of this script
export GMT_SESSION_NAME=$$	# Set a unique session name

lon1=12.7
lon2=13.7
lat1=42.4
lat2=43.2

lon_range=8 # lon_range=8i
lat_range=$(printf "%.3f" `echo "scale=4;($lat2-$lat1)*$lon_range/($lon2-$lon1)"|bc`)
lon_range=`echo $lon_range|awk '{print $1"i"}'`
lat_range=`echo $lat_range|awk '{print $1"i"}'`

projection="X$lon_range/$lat_range"
region="$lon1/$lon2/$lat1/$lat2"

gmt begin sta_eq jpg
gmt basemap -J$projection -R$region -Bxa0.2 -Bya0.2 -BWSen
cat catalog.dat|gawk  '{print $3, $2}'| gmt plot -Sc0.35c -W0.3p,black -Gred
cat station.dat|gawk  '{print $1, $2}'| gmt plot -St0.35c -W0.3p,black -Gblue
gmt end show
