#!/bin/bash -w

# Run NLLoc over split NLLOC_OBS event files in parallel.

CONTROL_FILE=${1:-nlloc.in}
PROJECT_NAME=${2:-LOCFLOW}
NUM_CORES=${3:-4}
OBS_GLOB=${4:-obs_files/*.nlloc_obs}
TIME_ROOT=${5:-time/layer}
OUT_ROOT=${6:-loc/${PROJECT_NAME}}
SWAP_BYTES=0
OBS_FILE_TYPE=NLLOC_OBS
LOCMETH=${LOCMETH:-"EDT_OT_WT 9999.0 4 -1 -1 -1.0 -1 -1 1"}

mkdir -p tmp "$OUT_ROOT"
rm -rf tmp/obsfiles_* tmp/"${PROJECT_NAME}"_nll.in*

SKELETON_CONF=tmp/NLL.cluster_SKELETON.conf
sed \
    -e '/^[[:space:]]*LOCFILES/ s/^/#/' \
    -e '/^[[:space:]]*LOCMETH/ s/^/#/' \
    "$CONTROL_FILE" > "$SKELETON_CONF"

shopt -s nullglob
obs_files=( $OBS_GLOB )
if [[ ${#obs_files[@]} -eq 0 ]]
then
    echo "No observation files match: $OBS_GLOB"
    exit 1
fi

if ((NUM_CORES < 1))
then
    NUM_CORES=1
fi

for ((i = 0; i < NUM_CORES; i++))
do
    mkdir -p "tmp/obsfiles_${i}"
done

idx=0
for obs_file in "${obs_files[@]}"
do
    bucket=$((idx % NUM_CORES))
    cp -p "$obs_file" "tmp/obsfiles_${bucket}/"
    idx=$((idx + 1))
done

PIDS=()
for ((i = 0; i < NUM_CORES; i++))
do
    if ! compgen -G "tmp/obsfiles_${i}/*.nlloc_obs" >/dev/null
    then
        continue
    fi

    control_tmp="tmp/${PROJECT_NAME}_nll.in_${i}"
    cp "$SKELETON_CONF" "$control_tmp"
    cat << END >> "$control_tmp"
LOCFILES tmp/obsfiles_${i}/* ${OBS_FILE_TYPE} ${TIME_ROOT} ${OUT_ROOT}_${i}/${PROJECT_NAME} ${SWAP_BYTES}
LOCMETH ${LOCMETH}
END

    mkdir -p "${OUT_ROOT}_${i}"
    NLLoc "$control_tmp" &
    PIDS+=($!)
done

for pid in "${PIDS[@]}"
do
    wait "$pid" || exit 1
done

for partial in "${OUT_ROOT}"_*
do
    [[ -d "$partial" ]] || continue
    cp -a "$partial"/. "$OUT_ROOT"/
done

hyp_files=( "${OUT_ROOT}"_*/"${PROJECT_NAME}".sum.grid0.loc.hyp )
if [[ ${#hyp_files[@]} -gt 0 ]]
then
    cat "${hyp_files[@]}" > "${OUT_ROOT}/${PROJECT_NAME}.sum.grid0.loc.hyp"
fi

for suffix in stations stat stat_totcorr
do
    files=( "${OUT_ROOT}"_*/"${PROJECT_NAME}".sum.grid0.loc.${suffix} )
    if [[ ${#files[@]} -gt 0 ]]
    then
        cat "${files[@]}" > "${OUT_ROOT}/${PROJECT_NAME}.sum.grid0.loc.${suffix}"
    fi
done

echo "${OUT_ROOT}/${PROJECT_NAME}.sum.grid0.loc.hyp"
