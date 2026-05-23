#!/usr/bin/env python3
"""Prepare NonLinLoc inputs from LOC-FLOW/REAL outputs."""

from __future__ import annotations

import argparse
import glob
import math
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


PHASE_ERRORS = {"P": 0.02, "S": 0.04}
DEFAULT_SIGMA_CAP = 0.50


@dataclass
class Pick:
    station: str
    phase: str
    arrival: datetime
    probability: str = "1.000"
    residual: float | None = None


@dataclass
class Event:
    event_id: str
    origin: datetime
    picks: list[Pick] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create NonLinLoc station, phase, velocity, and control files."
    )
    parser.add_argument(
        "--phase-file",
        default="../REAL/phase_allday.txt",
        help=(
            "REAL phase file. Supports phase_allday.txt or a glob such as "
            "../REAL/*.phase_sel.txt. Use phase_sel files for residual-based errors."
        ),
    )
    parser.add_argument("--station-file", default="../Data/station.dat")
    parser.add_argument("--velocity-file", default="../REAL/tt_db/mymodel.nd")
    parser.add_argument("--station-output", default="obs/station_coordinates.txt")
    parser.add_argument("--phase-output", default="obs/phases.obs")
    parser.add_argument("--split-dir", default="obs_files")
    parser.add_argument("--velocity-output", default="run/vel_model.nd")
    parser.add_argument("--control-output", default="nlloc.in")
    parser.add_argument("--ssst-control-output", default="loc2ssst.in")
    parser.add_argument("--project-name", default="LOCFLOW")
    parser.add_argument(
        "--station-prefix",
        default="auto",
        help="Use 'auto' to prefix numeric station codes with ST, 'none' for original names, or a literal prefix.",
    )
    parser.add_argument("--trans-lat", type=float)
    parser.add_argument("--trans-lon", type=float)
    parser.add_argument(
        "--datum-shift",
        type=float,
        default=0.0,
        help="Depth shift in km subtracted from the velocity model depths.",
    )
    parser.add_argument(
        "--top-depth",
        type=float,
        default=-2.0,
        help="Optional shallow top layer depth in km. Use a large value to disable.",
    )
    parser.add_argument(
        "--p-error",
        type=float,
        default=PHASE_ERRORS["P"],
        help="P uncertainty in fixed mode, or minimum P uncertainty floor in residual/auto mode.",
    )
    parser.add_argument(
        "--s-error",
        type=float,
        default=PHASE_ERRORS["S"],
        help="S uncertainty in fixed mode, or minimum S uncertainty floor in residual/auto mode.",
    )
    parser.add_argument(
        "--error-mode",
        choices=("fixed", "residual", "auto"),
        default="fixed",
        help=(
            "Pick uncertainty policy: fixed uses --p-error/--s-error for every pick; "
            "residual uses bounded abs(REAL phase_sel residual); auto uses residuals "
            "when present and fixed values otherwise."
        ),
    )
    parser.add_argument(
        "--sigma-cap",
        type=float,
        default=DEFAULT_SIGMA_CAP,
        help="Maximum pick uncertainty in seconds when --error-mode uses residuals.",
    )
    parser.add_argument(
        "--vggrid",
        default="2 151 65 0.0 0.0 -2.0 1.0 1.0 1.0 SLOW_LEN",
        help="VGGRID arguments after the keyword.",
    )
    parser.add_argument(
        "--locgrid",
        default="101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 PROB_DENSITY SAVE",
        help="LOCGRID arguments after the keyword.",
    )
    parser.add_argument(
        "--ssst-grid",
        default="101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 SSST_TIMECORR FLOAT",
        help="LSGRID arguments after the keyword.",
    )
    parser.add_argument(
        "--ssst-out-grid",
        default="101 101 33 -50.0 -50.0 -2.0 1.0 1.0 1.0 TIME FLOAT",
        help="LSOUTGRID arguments after the keyword.",
    )
    parser.add_argument(
        "--locsearch",
        default="OCT 40 40 8 0.01 50000 5000 0 1",
        help="LOCSEARCH arguments after the keyword.",
    )
    parser.add_argument(
        "--locmeth",
        default="EDT_OT_WT 9999.0 4 -1 -1 -1.0 -1 -1 1",
        help="LOCMETH arguments after the keyword.",
    )
    parser.add_argument("--locgau", default="0.5 0.0")
    parser.add_argument("--locgau2", default="0.02 0.05 2.0")
    parser.add_argument("--ssst-phstat", default="0.35 12 135.0 1.0 1.0 5.0")
    parser.add_argument("--delay-include", default="")
    return parser.parse_args()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def datetime_from_parts(
    year: str, month: str, day: str, hour: str, minute: str, seconds: str
) -> datetime:
    sec_float = float(seconds)
    sec_int = math.floor(sec_float)
    micro = round((sec_float - sec_int) * 1_000_000)
    base = datetime(int(year), int(month), int(day), int(hour), int(minute), 0)
    return base + timedelta(seconds=sec_int, microseconds=micro)


def station_label(station: str, prefix: str) -> str:
    prefix_norm = prefix.strip()
    if prefix_norm.lower() in {"", "none"}:
        return station
    if prefix_norm.lower() == "auto":
        return f"ST{station}" if station and station[0].isdigit() else station
    return f"{prefix_norm}{station}"


def read_stations(station_file: Path, station_prefix: str) -> tuple[dict[str, str], float, float]:
    stations: dict[str, str] = {}
    lats: list[float] = []
    lons: list[float] = []

    with station_file.open() as handle:
        for line in handle:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            lon, lat, _net, sta, _comp, elev = parts[:6]
            label = station_label(sta, station_prefix)
            stations[sta] = label
            lats.append(float(lat))
            lons.append(float(lon))

    if not stations:
        raise ValueError(f"No stations read from {station_file}")

    return stations, sum(lats) / len(lats), sum(lons) / len(lons)


def write_station_file(
    station_file: Path, output_file: Path, station_prefix: str
) -> tuple[dict[str, str], float, float]:
    station_map, lat_ref, lon_ref = read_stations(station_file, station_prefix)
    ensure_parent(output_file)

    with station_file.open() as source, output_file.open("w") as out:
        out.write("#GTSRCE  label  type  lat  lon  z_srce  elev\n")
        for line in source:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            lon, lat, _net, sta, _comp, elev = parts[:6]
            label = station_map[sta]
            out.write(
                f"GTSRCE  {label:<8s} LATLON  {float(lat):9.5f} "
                f"{float(lon):10.5f}  0.0  {float(elev):.3f}\n"
            )

    return station_map, lat_ref, lon_ref


def is_raw_event_header(parts: list[str]) -> bool:
    return (
        len(parts) >= 11
        and parts[0].lstrip("+-").isdigit()
        and parts[1].isdigit()
        and len(parts[1]) == 4
        and ":" in parts[4]
    )


def parse_event_header(line: str) -> tuple[Event, str]:
    parts = line.split()
    if line.lstrip().startswith("#"):
        # REAL/phase_allday.txt:
        # # year mon day hour min sec lat lon dep mag EH EZ RMS event_id
        event_id = parts[-1]
        origin = datetime_from_parts(parts[1], parts[2], parts[3], parts[4], parts[5], parts[6])
        return Event(event_id=event_id, origin=origin), "hash"

    # REAL/*.phase_sel.txt:
    # no year mon day HH:MM:SS.sss dtime std lat lon dep mag ...
    hour, minute, seconds = parts[4].split(":")
    origin = datetime_from_parts(parts[1], parts[2], parts[3], hour, minute, seconds)
    return Event(event_id=parts[0], origin=origin), "raw"


def float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def append_pick(event: Event, line: str, event_format: str) -> None:
    parts = line.split()
    if not parts:
        return

    if event_format == "raw" or (len(parts) >= 9 and parts[2] in {"P", "S"}):
        # Raw REAL pick line:
        # net station phase absolute_seconds travel_time amplitude residual probability baz
        if len(parts) < 5 or parts[2] not in {"P", "S"}:
            return
        station = parts[1]
        phase = parts[2]
        arrival = datetime(event.origin.year, event.origin.month, event.origin.day) + timedelta(
            seconds=float(parts[3])
        )
        residual = float_or_none(parts[6]) if len(parts) > 6 else None
        probability = parts[7] if len(parts) > 7 else "1.000"
    else:
        # Normalized REAL/phase_allday.txt pick line:
        # station travel_time probability phase
        if len(parts) < 4 or parts[3] not in {"P", "S"}:
            return
        station = parts[0]
        phase = parts[3]
        arrival = event.origin + timedelta(seconds=float(parts[1]))
        probability = parts[2]
        residual = None

    event.picks.append(
        Pick(
            station=station,
            phase=phase,
            arrival=arrival,
            probability=probability,
            residual=residual,
        )
    )


def parse_phase_file(phase_file: Path) -> list[Event]:
    events: list[Event] = []
    current: Event | None = None
    current_format = "hash"

    with phase_file.open() as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split()
            if line.lstrip().startswith("#") or is_raw_event_header(parts):
                if current is not None:
                    events.append(current)
                current, current_format = parse_event_header(line)
                continue
            if current is not None:
                append_pick(current, line, current_format)

    if current is not None:
        events.append(current)

    return [event for event in events if event.picks]


def expand_phase_files(phase_file: str) -> list[Path]:
    if glob.has_magic(phase_file):
        phase_files = [Path(path) for path in sorted(glob.glob(phase_file))]
    else:
        phase_files = [Path(phase_file)]

    if not phase_files:
        raise FileNotFoundError(phase_file)

    missing = [str(path) for path in phase_files if not path.exists()]
    if missing:
        raise FileNotFoundError(", ".join(missing))

    return phase_files


def parse_phase_files(phase_files: list[Path]) -> list[Event]:
    events: list[Event] = []
    for phase_file in phase_files:
        events.extend(parse_phase_file(phase_file))
    return events


def nlloc_time_fields(arrival: datetime) -> tuple[str, str, str]:
    date_text = arrival.strftime("%Y%m%d")
    hour_minute = arrival.strftime("%H%M")
    sec = arrival.second + arrival.microsecond / 1_000_000
    return date_text, hour_minute, f"{sec:07.4f}"


def pick_uncertainty(
    pick: Pick,
    p_error: float,
    s_error: float,
    error_mode: str,
    sigma_cap: float,
) -> float:
    floor = p_error if pick.phase == "P" else s_error
    if error_mode == "fixed":
        return floor
    if pick.residual is None:
        if error_mode == "auto":
            return floor
        raise ValueError(
            "--error-mode residual requires REAL phase_sel input with residual values; "
            f"pick {pick.station} {pick.phase} has no residual"
        )
    if not math.isfinite(pick.residual):
        return floor
    return min(max(abs(pick.residual), floor), sigma_cap)


def validate_error_options(
    events: list[Event],
    error_mode: str,
    p_error: float,
    s_error: float,
    sigma_cap: float,
) -> None:
    if p_error <= 0.0 or s_error <= 0.0:
        raise ValueError("--p-error and --s-error must be positive")
    if sigma_cap <= 0.0:
        raise ValueError("--sigma-cap must be positive")
    if error_mode in {"residual", "auto"} and sigma_cap < max(p_error, s_error):
        raise ValueError("--sigma-cap must be greater than or equal to --p-error and --s-error")

    pick_count = sum(len(event.picks) for event in events)
    residual_count = sum(
        1 for event in events for pick in event.picks if pick.residual is not None
    )
    if error_mode == "residual" and residual_count < pick_count:
        raise ValueError(
            "--error-mode residual requires REAL phase_sel input. "
            f"Only {residual_count} of {pick_count} picks have residual values."
        )


def format_pick(
    pick: Pick,
    station_map: dict[str, str],
    p_error: float,
    s_error: float,
    error_mode: str,
    sigma_cap: float,
) -> str:
    label = station_map.get(pick.station, station_label(pick.station, "auto"))
    date_text, hour_minute, second_text = nlloc_time_fields(pick.arrival)
    error = pick_uncertainty(pick, p_error, s_error, error_mode, sigma_cap)
    return (
        f"{label:<8s} ?    ?    ? {pick.phase:<1s}      ? "
        f"{date_text} {hour_minute}   {second_text} GAU  {error:.2e} "
        "-1.00e+00 -1.00e+00 -1.00e+00\n"
    )


def write_phase_files(
    events: list[Event],
    phase_output: Path,
    split_dir: Path,
    station_map: dict[str, str],
    p_error: float,
    s_error: float,
    error_mode: str,
    sigma_cap: float,
) -> None:
    ensure_parent(phase_output)
    split_dir.mkdir(parents=True, exist_ok=True)
    for old_file in split_dir.glob("*.nlloc_obs"):
        old_file.unlink()

    with phase_output.open("w") as combined:
        for index, event in enumerate(events, start=1):
            block = "".join(
                format_pick(pick, station_map, p_error, s_error, error_mode, sigma_cap)
                for pick in event.picks
            )
            if index > 1:
                combined.write("\n")
            combined.write(block)
            (split_dir / f"Event_{index:06d}.nlloc_obs").write_text(block)


def first_float(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def write_velocity_file(
    velocity_file: Path, output_file: Path, datum_shift: float, top_depth: float
) -> int:
    ensure_parent(output_file)
    layer_count = 0
    first_layer: tuple[float, float, float, float] | None = None

    with velocity_file.open() as source, output_file.open("w") as out:
        for line in source:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split()
            depth = first_float(parts[0])
            if depth is None:
                break
            vp = float(parts[1])
            vs = float(parts[2])
            density = float(parts[3]) if len(parts) > 3 else 2.6
            shifted_depth = depth - datum_shift

            if first_layer is None:
                first_layer = (shifted_depth, vp, vs, density)
                if top_depth < shifted_depth:
                    out.write(
                        f"LAYER  {top_depth:8.4f}  {vp:7.4f}  0  "
                        f"{vs:7.4f}  0  {density:6.4f}  0\n"
                    )
                    layer_count += 1

            out.write(
                f"LAYER  {shifted_depth:8.4f}  {vp:7.4f}  0  "
                f"{vs:7.4f}  0  {density:6.4f}  0\n"
            )
            layer_count += 1

    if layer_count == 0:
        raise ValueError(f"No velocity layers read from {velocity_file}")

    return layer_count


def write_control_file(args: argparse.Namespace, trans_lat: float, trans_lon: float) -> None:
    control_file = Path(args.control_output)
    ensure_parent(control_file)

    delay_include = f"INCLUDE {args.delay_include}\n" if args.delay_include else ""

    text = f"""# =============================================================================
# NonLinLoc control file generated from REAL association output
# =============================================================================
CONTROL 1 54321

TRANS AZIMUTHAL_EQUIDIST WGS-84 {trans_lat:.5f} {trans_lon:.5f} 0

# =============================================================================
# Vel2Grid input
# =============================================================================
VGOUT model/layer
VGTYPE P
VGTYPE S
VGGRID {args.vggrid}
INCLUDE {Path(args.velocity_output).as_posix()}

# =============================================================================
# Grid2Time input
# =============================================================================
GTFILES model/layer time/layer P 0
GTMODE GRID2D ANGLES_YES
INCLUDE {Path(args.station_output).as_posix()}
GT_PLFD 1.0e-3 0

# =============================================================================
# NLLoc input
# =============================================================================
LOCSIG LOC-FLOW NonLinLoc
LOCCOM REAL phase association relocation
LOCFILES {Path(args.phase_output).as_posix()} NLLOC_OBS time/layer loc/{args.project_name} 0
LOCHYPOUT SAVE_NLLOC_ALL SAVE_NLLOC_SUM NLL_FORMAT_VER_2
LOCSEARCH {args.locsearch}
LOCGRID {args.locgrid}
LOCMETH {args.locmeth}
LOCGAU {args.locgau}
LOCGAU2 {args.locgau2}
LOCSTAWT 0 1.0
LOCPHASEID P P Pg Pn
LOCPHASEID S S Sg Sn
LOCQUAL2ERR 0.1 0.4 1.0 99999.9 99999.9
LOCANGLES ANGLES_YES 5
LOCPHSTAT 9999.0 -1 9999.0 2.0 2.0 9999.9 -9999.9 9999.9
{delay_include}"""

    control_file.write_text(text)


def write_ssst_control_file(args: argparse.Namespace, trans_lat: float, trans_lon: float) -> None:
    control_file = Path(args.ssst_control_output)
    ensure_parent(control_file)

    text = f"""# =============================================================================
# Loc2ssst control file generated from REAL association output
# =============================================================================
CONTROL 1 54321

TRANS AZIMUTHAL_EQUIDIST WGS-84 {trans_lat:.5f} {trans_lon:.5f} 0

# =============================================================================
# Loc2ssst input
# =============================================================================
LSGRID {args.ssst_grid}
LSOUTGRID {args.ssst_out_grid}
LOCPHSTAT {args.ssst_phstat}
LOCPHASEID P P Pg Pn
LOCPHASEID S S Sg Sn
"""

    control_file.write_text(text)


def main() -> None:
    args = parse_args()
    phase_files = expand_phase_files(args.phase_file)
    station_file = Path(args.station_file)
    velocity_file = Path(args.velocity_file)

    if not station_file.exists():
        raise FileNotFoundError(station_file)
    if not velocity_file.exists():
        raise FileNotFoundError(velocity_file)

    for directory in ["model", "time", "loc"]:
        Path(directory).mkdir(exist_ok=True)

    station_map, auto_lat, auto_lon = write_station_file(
        station_file, Path(args.station_output), args.station_prefix
    )
    trans_lat = args.trans_lat if args.trans_lat is not None else auto_lat
    trans_lon = args.trans_lon if args.trans_lon is not None else auto_lon

    events = parse_phase_files(phase_files)
    validate_error_options(
        events,
        args.error_mode,
        args.p_error,
        args.s_error,
        args.sigma_cap,
    )
    write_phase_files(
        events,
        Path(args.phase_output),
        Path(args.split_dir),
        station_map,
        args.p_error,
        args.s_error,
        args.error_mode,
        args.sigma_cap,
    )
    layer_count = write_velocity_file(
        velocity_file, Path(args.velocity_output), args.datum_shift, args.top_depth
    )
    write_control_file(args, trans_lat, trans_lon)
    write_ssst_control_file(args, trans_lat, trans_lon)

    map_file = Path(args.station_output).with_name("station_map.txt")
    ensure_parent(map_file)
    with map_file.open("w") as out:
        for original, label in sorted(station_map.items()):
            out.write(f"{original} {label}\n")

    # Remove stale run products that can otherwise be mistaken for current output.
    for stale in Path("loc").glob(f"{args.project_name}.sum.grid0.loc.*"):
        if stale.is_file():
            stale.unlink()
        elif stale.is_dir():
            shutil.rmtree(stale)

    pick_count = sum(len(event.picks) for event in events)
    residual_count = sum(
        1 for event in events for pick in event.picks if pick.residual is not None
    )
    print(f"stations: {len(station_map)} -> {args.station_output}")
    print(f"phase files: {len(phase_files)}")
    print(f"events: {len(events)}, picks: {pick_count} -> {args.phase_output}")
    print(
        f"pick uncertainty mode: {args.error_mode} "
        f"(residual picks: {residual_count}/{pick_count}, sigma cap: {args.sigma_cap:.3f} s)"
    )
    print(f"split event files -> {args.split_dir}")
    print(f"velocity layers: {layer_count} -> {args.velocity_output}")
    print(f"control file -> {args.control_output}")
    print(f"SSST control file -> {args.ssst_control_output}")


if __name__ == "__main__":
    main()
