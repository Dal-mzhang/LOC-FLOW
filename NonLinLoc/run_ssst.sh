#!/bin/bash -w

# Run Loc2ssst in station batches. Station labels are read from the generated
# GTSRCE station file.

CONTROL_FILE=${1:-loc2ssst.in}
STATION_FILE=${2:-obs/station_coordinates.txt}
NUM_CORES=${3:-4}

command -v Loc2ssst >/dev/null 2>&1 || { echo 'Loc2ssst not found in PATH'; exit 1; }

if [[ ! -f "$CONTROL_FILE" ]]
then
    echo "Control file not found: $CONTROL_FILE"
    exit 1
fi

if [[ ! -f "$STATION_FILE" ]]
then
    echo "Station file not found: $STATION_FILE"
    exit 1
fi

if ((NUM_CORES < 1))
then
    NUM_CORES=1
fi

mkdir -p tmp
awk '$1 == "GTSRCE" {print $2}' "$STATION_FILE" > tmp/ssst_stations.txt

COUNT=$(wc -l < tmp/ssst_stations.txt)
if ((COUNT < 1))
then
    echo "No GTSRCE stations found in $STATION_FILE"
    exit 1
fi

rm -f tmp/ssst_sta_*
split -l $((1 + COUNT / NUM_CORES)) tmp/ssst_stations.txt tmp/ssst_sta_

PIDS=()
INDEX=0
for STATION_LIST in tmp/ssst_sta_*
do
    [[ -s "$STATION_LIST" ]] || continue
    STA_SET=$(paste -sd= "$STATION_LIST")
    control_tmp="tmp/ssst_${INDEX}.in"
    cp "$CONTROL_FILE" "$control_tmp"
    cat << END >> "$control_tmp"
LSSTATIONS ${STA_SET}
END
    echo "Running Loc2ssst batch ${INDEX}"
    Loc2ssst "$control_tmp" &
    PIDS+=($!)
    INDEX=$((INDEX + 1))
done

for PID in "${PIDS[@]}"
do
    wait "$PID" || exit 1
done
