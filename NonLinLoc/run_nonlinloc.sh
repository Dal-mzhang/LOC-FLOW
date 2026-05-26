#!/bin/bash

# Run NonLinLoc after REAL association.
# Edit the variables below for your study area before running.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"

if [[ -n "${NLL_BIN_DIR:-}" ]]
then
    nll_bin_candidates=("$NLL_BIN_DIR")
else
    nll_bin_candidates=("$repo_dir/bin" "$repo_dir/src/NonLinLoc/src/bin" "$repo_dir/src/NonLinLoc/www_beta/bin")
fi

for nll_bin_dir in "${nll_bin_candidates[@]}"
do
    if [[ -x "$nll_bin_dir/Vel2Grid" && -x "$nll_bin_dir/Grid2Time" && -x "$nll_bin_dir/NLLoc" ]]
    then
        export PATH="$nll_bin_dir:$PATH"
        break
    fi
done

if ! command -v Vel2Grid >/dev/null 2>&1 && [[ -d "$repo_dir/src/NonLinLoc/src" ]]
then
    echo "NonLinLoc binaries not found. Build them with:"
    echo "  cmake -S ../src/NonLinLoc/src -B ../src/NonLinLoc/src/build"
    echo "  cmake --build ../src/NonLinLoc/src/build --target Vel2Grid Grid2Time NLLoc -j"
fi

phasein="../REAL/*.phase_sel.txt"
stationin="../Data/station.dat"
velocityin="../REAL/tt_db/mymodel.nd"

project_name="LOCFLOW"
control="nlloc.in"

# Use "auto" to keep normal station names and prefix numeric station names with ST.
station_prefix="auto"

# Set these to explicit values if you do not want the station centroid.
latref="auto"
lonref="auto"

# Shift velocity depths upward by this value in km, e.g. 0.94515 for the
datum_shift=0.0
top_depth=-2.0

# Default grids are conservative starting points. Tighten/refine for final runs.
# Grid2Time's Podvin-Lecomte solver requires cubic cells, so keep dx=dy=dz.
# The GRID2D radial extent is 150 km so stations outside the search grid still
# have valid travel times to the far corners of the default location grid.
# The -2 km top keeps all current stations inside the grid after elevation is
# applied as a positive-up offset.
vggrid="2 151 65 0.0 0.0 -2.0 1.0 1.0 1.0 SLOW_LEN"
locgrid="101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 PROB_DENSITY SAVE"
locsearch="OCT 40 40 8 0.01 50000 5000 0 1"
locmeth="EDT_OT_WT 9999.0 4 -1 -1 -1.0 -1 -1 1"
locgau="0.5 0.0"
locgau2="0.02 0.05 2.0"

# Pick-time uncertainties in seconds for the NLLOC_OBS GAU records.
# In residual mode, p_error and s_error are minimum floors and sigma_cap is
# the maximum bounded uncertainty from abs(REAL phase_sel residual).
error_mode="residual"
p_error=0.02
s_error=0.04
sigma_cap=0.50

# Optional station delay file with LOCDELAY statements.
delay_include=""

run_grid=1
run_location=1
run_parallel=0
num_cores=4

coord_args=()
if [[ "$latref" != "auto" ]]; then
    coord_args+=(--trans-lat "$latref")
fi
if [[ "$lonref" != "auto" ]]; then
    coord_args+=(--trans-lon "$lonref")
fi

delay_args=()
if [[ -n "$delay_include" ]]; then
    delay_args+=(--delay-include "$delay_include")
fi

python3 prepare_nonlinloc.py \
    --phase-file "$phasein" \
    --station-file "$stationin" \
    --velocity-file "$velocityin" \
    --project-name "$project_name" \
    --control-output "$control" \
    --station-prefix "$station_prefix" \
    --datum-shift "$datum_shift" \
    --top-depth "$top_depth" \
    --error-mode "$error_mode" \
    --p-error "$p_error" \
    --s-error "$s_error" \
    --sigma-cap "$sigma_cap" \
    --vggrid "$vggrid" \
    --locgrid "$locgrid" \
    --locsearch "$locsearch" \
    --locmeth "$locmeth" \
    --locgau "$locgau" \
    --locgau2 "$locgau2" \
    "${coord_args[@]}" \
    "${delay_args[@]}" || { echo 'Error preparing NonLinLoc input files'; exit 1; }

if (($run_grid == 1))
then
    command -v Vel2Grid >/dev/null 2>&1 || { echo 'Vel2Grid not found in PATH'; exit 1; }
    command -v Grid2Time >/dev/null 2>&1 || { echo 'Grid2Time not found in PATH'; exit 1; }

    rm -f model/layer.* time/layer.*

    echo 'generating NonLinLoc model grid ...'
    Vel2Grid "$control" || { echo 'Error running Vel2Grid'; exit 1; }

    echo 'generating NonLinLoc travel-time grids ...'
    mkdir -p tmp
    for phase in P S
    do
        phase_control="tmp/Grid2Time_${phase}.in"
        sed "s#^GTFILES .*#GTFILES model/layer time/layer ${phase} 0#" "$control" > "$phase_control"
        Grid2Time "$phase_control" || { echo "Error running Grid2Time for ${phase}"; exit 1; }
    done
else
    echo 'NonLinLoc grid generation skipped'
fi

if (($run_location == 1))
then
    command -v NLLoc >/dev/null 2>&1 || { echo 'NLLoc not found in PATH'; exit 1; }

    if (($run_parallel == 1))
    then
        bash run_nll_parallel.sh "$control" "$project_name" "$num_cores" || { echo 'Error running NLLoc in parallel'; exit 1; }
    else
        echo 'running NonLinLoc locations ...'
        mkdir -p loc
        NLLoc "$control" || { echo 'Error running NLLoc'; exit 1; }
    fi

    hypout="loc/${project_name}.sum.grid0.loc.hyp"
    csvout="loc/${project_name}.sum.grid0.loc.csv"
    if [[ -f "$hypout" ]]
    then
        python3 nlloc_hyp_to_csv.py "$hypout" "$csvout" || { echo 'Error converting NonLinLoc output CSV'; exit 1; }
    fi
else
    echo 'NonLinLoc location step skipped'
fi
