#!/bin/bash -w

# Iterative NonLinLoc + Loc2ssst SSST relocation.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"

# src/run_install.sh stages REAL and NonLinLoc binaries into the repository bin directory.
nll_bin_dir=${NLL_BIN_DIR:-"$repo_dir/bin"}
if [[ -d "$nll_bin_dir" ]]
then
    export PATH="$nll_bin_dir:$PATH"
else
    echo "NonLinLoc binary directory not found: $nll_bin_dir"
    echo "Stage binaries with: cd \"$repo_dir/src\" && bash run_install.sh"
fi

phasein=${phasein:-"../REAL/*.phase_sel.txt"}
stationin=${stationin:-"../Data/station.dat"}
velocityin=${velocityin:-"../REAL/tt_db/mymodel.nd"}

project_name=${project_name:-"LOCFLOW"}
run_name=${run_name:-"SSST"}
model_name=${model_name:-"layer"}
control=${control:-"nlloc.in"}
ssst_control=${ssst_control:-"loc2ssst.in"}

station_prefix=${station_prefix:-"auto"}
latref=${latref:-"auto"}
lonref=${lonref:-"auto"}
datum_shift=${datum_shift:-0.0}
top_depth=${top_depth:--2.0}

vggrid=${vggrid:-"2 151 65 0.0 0.0 -2.0 1.0 1.0 1.0 SLOW_LEN"}
locgrid=${locgrid:-"101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 PROB_DENSITY SAVE"}
ssst_grid=${ssst_grid:-"101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 SSST_TIMECORR FLOAT"}
ssst_out_grid=${ssst_out_grid:-"101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 TIME FLOAT"}
locsearch=${locsearch:-"OCT 40 40 8 0.01 50000 5000 0 1"}
locmeth=${locmeth:-"EDT_OT_WT 9999.0 4 -1 -1 -1.0 -1 -1 1"}
vpvs=${vpvs:--1.0}

error_mode=${error_mode:-"residual"}
p_error=${p_error:-0.02}
s_error=${s_error:-0.04}
sigma_cap=${sigma_cap:-0.50}
ssst_phstat=${ssst_phstat:-"0.35 12 135.0 1.0 1.0 5.0"}

run_grid=${run_grid:-1}
num_cores=${num_cores:-4}
iteration_start=${1:-0}
iteration_max=${2:-3}
char_dist=${3:-9999}
char_dist_start=${char_dist_start:-16}
char_dist_divisor=${char_dist_divisor:-2}
char_dist_min=${char_dist_min:-1}
char_dist_scale=${char_dist_scale:-1}
min_num_phases_loc=${min_num_phases_loc:-4}

if ((num_cores < 1))
then
    num_cores=1
fi

coord_args=()
if [[ "$latref" != "auto" ]]; then
    coord_args+=(--trans-lat "$latref")
fi
if [[ "$lonref" != "auto" ]]; then
    coord_args+=(--trans-lon "$lonref")
fi

python3 prepare_nonlinloc.py \
    --phase-file "$phasein" \
    --station-file "$stationin" \
    --velocity-file "$velocityin" \
    --project-name "$project_name" \
    --control-output "$control" \
    --ssst-control-output "$ssst_control" \
    --station-prefix "$station_prefix" \
    --datum-shift "$datum_shift" \
    --top-depth "$top_depth" \
    --error-mode "$error_mode" \
    --p-error "$p_error" \
    --s-error "$s_error" \
    --sigma-cap "$sigma_cap" \
    --vggrid "$vggrid" \
    --locgrid "$locgrid" \
    --ssst-grid "$ssst_grid" \
    --ssst-out-grid "$ssst_out_grid" \
    --locsearch "$locsearch" \
    --locmeth "$locmeth" \
    --ssst-phstat "$ssst_phstat" \
    "${coord_args[@]}" || { echo 'Error preparing NonLinLoc SSST input files'; exit 1; }

command -v NLLoc >/dev/null 2>&1 || { echo 'NLLoc not found in PATH'; exit 1; }
command -v Loc2ssst >/dev/null 2>&1 || { echo 'Loc2ssst not found in PATH'; exit 1; }

if (($run_grid == 1))
then
    command -v Vel2Grid >/dev/null 2>&1 || { echo 'Vel2Grid not found in PATH'; exit 1; }
    command -v Grid2Time >/dev/null 2>&1 || { echo 'Grid2Time not found in PATH'; exit 1; }
    rm -f model/layer.* time/layer.*
    Vel2Grid "$control" || { echo 'Error running Vel2Grid'; exit 1; }
    mkdir -p tmp
    for phase in P S
    do
        phase_control="tmp/Grid2Time_${phase}.in"
        sed "s#^GTFILES .*#GTFILES model/layer time/layer ${phase} 0#" "$control" > "$phase_control"
        Grid2Time "$phase_control" || { echo "Error running Grid2Time for ${phase}"; exit 1; }
    done
fi

mkdir -p tmp out
rm -rf "out/${run_name}"
mkdir -p "out/${run_name}"

sed \
    -e '/^[[:space:]]*LOCFILES/ s/^/#/' \
    -e '/^[[:space:]]*LOCMETH/ s/^/#/' \
    -e '/^[[:space:]]*LOCHYPOUT/ s/^/#/' \
    "$control" > tmp/NLL.cluster_SKELETON_SSST.conf

time_root="time/${model_name}"
iteration=${iteration_start}
iteration_final=$((iteration_max + 1))

while ((iteration <= iteration_final))
do
    out_root="out/${run_name}/loc_ssst_corr${iteration}"
    mkdir -p "$out_root"

    save_octree=""
    if ((iteration == iteration_final))
    then
        save_octree="SAVE_NLLOC_OCTREE SAVE_FMAMP"
    fi

    rm -rf tmp/obsfiles_* tmp/${project_name}_nll_*
    obs_files=(obs_files/*.nlloc_obs)
    if [[ ${#obs_files[@]} -eq 0 || ! -e "${obs_files[0]}" ]]
    then
        echo "No observation files found under obs_files/"
        exit 1
    fi

    for ((i = 0; i < num_cores; i++))
    do
        mkdir -p "tmp/obsfiles_${i}"
    done

    index=0
    for obs_file in "${obs_files[@]}"
    do
        bucket=$((index % num_cores))
        cp -p "$obs_file" "tmp/obsfiles_${bucket}/"
        index=$((index + 1))
    done

    PIDS=()
    HYP_FILES=()
    for ((i = 0; i < num_cores; i++))
    do
        compgen -G "tmp/obsfiles_${i}/*.nlloc_obs" >/dev/null || continue
        control_tmp="tmp/${project_name}_nll_${iteration}.in_${i}"
        cp tmp/NLL.cluster_SKELETON_SSST.conf "$control_tmp"
        cat << END >> "$control_tmp"
CONTROL 0 54321
LOCCOM ${run_name} loc_ssst_corr${iteration}
LOCFILES tmp/obsfiles_${i}/*.nlloc_obs NLLOC_OBS ${time_root} ${out_root}_${i}/${project_name} 0
LOCMETH EDT_OT_WT 9999.0 ${min_num_phases_loc} -1 -1 ${vpvs} -1 -1 1
LOCHYPOUT SAVE_NLLOC_ALL NLL_FORMAT_VER_2 ${save_octree}
END
        mkdir -p "${out_root}_${i}"
        NLLoc "$control_tmp" &
        PIDS+=($!)
        HYP_FILES+=("${out_root}_${i}/${project_name}.sum.grid0.loc.hyp")
    done

    for pid in "${PIDS[@]}"
    do
        wait "$pid" || exit 1
    done

    missing_hyp=()
    for hyp_file in "${HYP_FILES[@]}"
    do
        if [[ ! -s "$hyp_file" ]]
        then
            missing_hyp+=("$hyp_file")
        fi
    done

    if [[ ${#missing_hyp[@]} -gt 0 ]]
    then
        echo "Missing or empty NLLoc summary file(s):"
        printf '  %s\n' "${missing_hyp[@]}"
        exit 1
    fi

    for hyp_file in "${HYP_FILES[@]}"
    do
        cp -a "$(dirname "$hyp_file")"/. "$out_root"/
    done
    cat "${HYP_FILES[@]}" > "${out_root}/${project_name}.sum.grid0.loc.hyp"
    for suffix in stations stat stat_totcorr
    do
        files=()
        for hyp_file in "${HYP_FILES[@]}"
        do
            candidate="$(dirname "$hyp_file")/${project_name}.sum.grid0.loc.${suffix}"
            [[ -s "$candidate" ]] && files+=("$candidate")
        done
        if [[ ${#files[@]} -gt 0 ]]
        then
            cat "${files[@]}" > "${out_root}/${project_name}.sum.grid0.loc.${suffix}"
        fi
    done
    rm -rf "${out_root}"_*

    if ((iteration == iteration_final))
    then
        python3 nlloc_hyp_to_csv.py "${out_root}/${project_name}.sum.grid0.loc.hyp" "${out_root}/${project_name}.sum.grid0.loc.csv"
        echo "${out_root}/${project_name}.sum.grid0.loc.hyp" > ssst.list
        break
    fi

    char_dist_use=$(awk -v d="$char_dist" -v s="$char_dist_scale" 'BEGIN {printf "%.3f", d / s}')
    ssst_out_dir="out/${run_name}/ssst_corr${iteration}"
    mkdir -p "$ssst_out_dir"
    ln -sf "$(pwd)/${time_root}"*.time.* "$ssst_out_dir"/

    ssst_root="${ssst_out_dir}/${model_name}"
    ssst_tmp="tmp/${project_name}_ssst_${iteration}.in"
    cp "$ssst_control" "$ssst_tmp"
    lsmode="LSMODE ANGLES_NO"
    if ((iteration == iteration_max))
    then
        lsmode="LSMODE ANGLES_YES"
    fi
    cat << END >> "$ssst_tmp"
LSPARAMS ${char_dist_use} 0.0000001
${lsmode}
LSOUT ${ssst_root}
LSLOCFILES ${out_root}/${project_name}.*.*.grid0.loc.hyp
LOCFILES obs_files/*.nlloc_obs NLLOC_OBS ${time_root} ${out_root}/${project_name} 0
LOCMETH EDT_OT_WT 9999.0 ${min_num_phases_loc} -1 -1 ${vpvs} -1 -1 1
END
    bash run_ssst.sh "$ssst_tmp" obs/station_coordinates.txt "$num_cores" || { echo 'Error running Loc2ssst'; exit 1; }

    time_root="$ssst_root"
    vpvs=-9.99
    iteration=$((iteration + 1))

    if ((char_dist == 9999))
    then
        char_dist=$char_dist_start
    elif ((char_dist > char_dist_min))
    then
        char_dist=$((char_dist / char_dist_divisor))
    fi
done
