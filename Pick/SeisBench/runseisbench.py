#!/usr/bin/env python3
"""
Run SeisBench phase pickers and write LOC-FLOW/REAL-compatible pick files.

Default inputs follow the standard LOC-FLOW layout:
    Data/waveform_sac/YYYYMMDD/NET.STA.CHANNEL
    Data/station.dat

Default outputs are written under:
    Pick/SeisBench/picks/MODEL_WEIGHT/YYYYMMDD/NET.STA.P.txt
    Pick/SeisBench/picks/MODEL_WEIGHT/YYYYMMDD/NET.STA.S.txt

Each REAL pick line is:
    seconds_since_midnight probability amplitude
"""

from __future__ import annotations

import argparse
import csv
import glob
import inspect
import json
import multiprocessing
import os
import re
import shutil
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]

MODEL_ALIASES = {
    "phasenet": "PhaseNet",
    "pn": "PhaseNet",
    "eqtransformer": "EQTransformer",
    "eqt": "EQTransformer",
    "gpd": "GPD",
}

DEFAULT_MODEL_WEIGHTS = {
    "PhaseNet": "original",
    "EQTransformer": "original",
    "GPD": "original",
}

DEFAULT_THRESHOLDS = {
    "PhaseNet": (0.2, 0.2),
    "EQTransformer": (0.3, 0.3),
    "GPD": (0.98, 0.98),
}


@dataclass(frozen=True)
class Station:
    lon: Optional[float]
    lat: Optional[float]
    net: str
    sta: str
    channel: str
    elev: Optional[float] = None
    channels: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelSpec:
    name: str
    weights: str
    label: str


@dataclass(frozen=True)
class RuntimeConfig:
    data_dir: str
    output_dir: str
    results_dir: str
    file_template: str
    component_suffixes: Tuple[str, ...]
    exact_channels: Tuple[str, ...]
    min_components: int
    detrend: bool
    taper: float
    freqmin: Optional[float]
    freqmax: Optional[float]
    resample_rate: Optional[float]
    model_sampling_rate: Optional[float]
    start_second: float
    duration_seconds: float
    batch_size: int
    p_threshold: Optional[float]
    s_threshold: Optional[float]
    detection_threshold: Optional[float]
    segment_seconds: float
    default_amplitude: float
    save_csv: bool
    torch_threads: Optional[int]


_WORKER_CONFIG: Optional[RuntimeConfig] = None
_WORKER_MODELS: Dict[str, Tuple[ModelSpec, object]] = {}
_WORKER_DEVICE: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run SeisBench pickers and write LOC-FLOW REAL pick files."
    )
    parser.add_argument(
        "--data-dir",
        default=str(ROOT_DIR / "Data" / "waveform_sac"),
        help="Waveform root directory. Default: ../../Data/waveform_sac",
    )
    parser.add_argument(
        "--station-file",
        default=None,
        help=(
            "Station file. Supports LOC-FLOW station.dat/station_all.dat or "
            "EQTransformer-style station JSON. Default: auto-detect Data/station.dat, "
            "then Data/station_all.dat."
        ),
    )
    parser.add_argument(
        "--file-template",
        default="{date}/{net}.{station}.{channel}",
        help=(
            "Path template relative to --data-dir. Available fields: date, net, "
            "station, sta, channel. Default: {date}/{net}.{station}.{channel}"
        ),
    )
    parser.add_argument("--start-date", default="2016-10-14", help="Start date: YYYY-MM-DD or YYYYMMDD.")
    parser.add_argument("--end-date", default=None, help="Inclusive end date. Overrides --nday.")
    parser.add_argument("--nday", type=int, default=1, help="Number of days to process.")
    parser.add_argument(
        "--models",
        default="PhaseNet:original",
        help=(
            "Comma-separated SeisBench models, optionally with weights. Examples: "
            "PhaseNet, PhaseNet:stead, EQTransformer:original, GPD:original. "
            "PhaseNet_original is accepted as shorthand for PhaseNet:original. "
            "Use Model:weights@label to override the output folder name."
        ),
    )
    parser.add_argument(
        "--device",
        default="auto",
        help=(
            "Device selection: auto, cpu, cuda, cuda:0, cuda:0,cuda:1, or all. "
            "Default uses cuda:0 when available, otherwise cpu."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=(
            "Total worker processes. Default: 1 for cpu/cuda:0, or one worker per "
            "GPU when --device has multiple GPUs."
        ),
    )
    parser.add_argument("--torch-threads", type=int, default=None, help="Set torch CPU threads per worker.")
    parser.add_argument("--batch-size", type=int, default=1024, help="SeisBench classify batch size.")
    parser.add_argument("--p-threshold", type=float, default=None, help="Override P pick threshold.")
    parser.add_argument("--s-threshold", type=float, default=None, help="Override S pick threshold.")
    parser.add_argument(
        "--detection-threshold",
        type=float,
        default=None,
        help="Detection threshold for models that accept it, such as EQTransformer.",
    )
    parser.add_argument(
        "--segment-seconds",
        type=float,
        default=0.0,
        help="Classify each stream in fixed-length segments. Use 1800 for GPD-style half-hour chunks.",
    )
    parser.add_argument(
        "--component-suffixes",
        default="Z,N,E",
        help=(
            "Component suffixes appended to the station channel prefix from station.dat. "
            "Use Z,1,2 for OBS-style DHZ/DH1/DH2. Default: Z,N,E"
        ),
    )
    parser.add_argument(
        "--channels",
        default=None,
        help="Exact comma-separated channels to read for every station, overriding --component-suffixes.",
    )
    parser.add_argument(
        "--min-components",
        type=int,
        default=1,
        help="Minimum readable components required before running a station/day.",
    )
    parser.add_argument("--freqmin", type=float, default=None, help="Optional bandpass lower corner.")
    parser.add_argument("--freqmax", type=float, default=None, help="Optional bandpass upper corner.")
    parser.add_argument("--no-detrend", action="store_true", help="Disable demean/linear detrending.")
    parser.add_argument("--taper", type=float, default=0.001, help="Taper max percentage. Use 0 to disable.")
    parser.add_argument(
        "--resample-rate",
        type=float,
        default=None,
        help="Optional ObsPy interpolation rate before picking.",
    )
    parser.add_argument(
        "--model-sampling-rate",
        type=float,
        default=None,
        help="Optional override for model.sampling_rate.",
    )
    parser.add_argument("--start-second", type=float, default=0.0, help="Seconds after midnight to start.")
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=86400.0,
        help="Daily window length in seconds.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(SCRIPT_DIR / "picks"),
        help="REAL-compatible pick output directory. Default: Pick/SeisBench/picks",
    )
    parser.add_argument(
        "--results-dir",
        default=str(SCRIPT_DIR / "results"),
        help="Optional per-station CSV output directory, used only with --save-csv.",
    )
    parser.add_argument(
        "--default-amplitude",
        type=float,
        default=0.0,
        help="Amplitude written to REAL pick files when no amplitude is measured.",
    )
    parser.add_argument(
        "--save-csv",
        action="store_true",
        help="Also write per-station picking_result.csv files for debugging or later conversion.",
    )
    parser.add_argument("--no-save-csv", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not remove existing output date directories before processing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print resolved inputs without running SeisBench.",
    )
    return parser.parse_args()


def parse_date(value: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD or YYYYMMDD.")


def build_dates(start_date: str, nday: int, end_date: Optional[str]) -> List[str]:
    start = parse_date(start_date)
    if end_date:
        end = parse_date(end_date)
        if end < start:
            raise ValueError("--end-date must be on or after --start-date")
        count = (end - start).days + 1
    else:
        if nday < 1:
            raise ValueError("--nday must be >= 1")
        count = nday
    return [(start + timedelta(days=i)).strftime("%Y%m%d") for i in range(count)]


def resolve_station_file(path_arg: Optional[str]) -> Path:
    if path_arg:
        return Path(path_arg).expanduser().resolve()

    station_dat = ROOT_DIR / "Data" / "station.dat"
    station_all = ROOT_DIR / "Data" / "station_all.dat"
    if station_dat.exists():
        return station_dat
    return station_all


def parse_float(value: object) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_stations(path: Path) -> List[Station]:
    if not path.exists():
        raise FileNotFoundError(f"Station file not found: {path}")

    if path.suffix.lower() == ".json":
        with path.open() as f:
            payload = json.load(f)

        stations: List[Station] = []
        for sta, info in payload.items():
            channels = tuple(str(ch) for ch in info.get("channels", []) if ch)
            channel = channels[0] if channels else str(info.get("channel", "HHZ"))
            coords = info.get("coords", [])
            lat = parse_float(coords[0]) if len(coords) > 0 else parse_float(info.get("latitude"))
            lon = parse_float(coords[1]) if len(coords) > 1 else parse_float(info.get("longitude"))
            elev = parse_float(coords[2]) if len(coords) > 2 else parse_float(info.get("elevation"))
            stations.append(
                Station(
                    lon=lon,
                    lat=lat,
                    net=str(info.get("network", info.get("net", ""))),
                    sta=str(sta),
                    channel=channel,
                    elev=elev,
                    channels=channels,
                )
            )
        return stations

    stations = []
    with path.open() as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5:
                raise ValueError(f"{path}:{line_number}: expected at least 5 columns")
            lon, lat, net, sta, channel = parts[:5]
            elev = parts[5] if len(parts) > 5 else None
            stations.append(
                Station(
                    lon=parse_float(lon),
                    lat=parse_float(lat),
                    net=net,
                    sta=sta,
                    channel=channel,
                    elev=parse_float(elev),
                )
            )
    return stations


def normalize_model_name(name: str) -> str:
    key = name.strip()
    return MODEL_ALIASES.get(key.lower(), key)


def safe_label_part(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("_") or "default"


def build_model_label(name: str, weights: str) -> str:
    return f"{safe_label_part(name)}_{safe_label_part(weights)}"


def infer_model_and_weights(item: str) -> Tuple[str, str]:
    name = normalize_model_name(item)
    if name in DEFAULT_MODEL_WEIGHTS:
        return name, DEFAULT_MODEL_WEIGHTS[name]

    for model_name in DEFAULT_MODEL_WEIGHTS:
        prefix = f"{model_name}_"
        if item.lower().startswith(prefix.lower()):
            return model_name, item[len(prefix) :]

    for alias, model_name in MODEL_ALIASES.items():
        prefix = f"{alias}_"
        if item.lower().startswith(prefix):
            return model_name, item[len(prefix) :]

    return name, DEFAULT_MODEL_WEIGHTS.get(name, "original")


def parse_models(value: str) -> Tuple[ModelSpec, ...]:
    specs = []
    labels = set()
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue

        explicit_label = None
        if "@" in item:
            item, explicit_label = item.rsplit("@", 1)
            item = item.strip()
            explicit_label = safe_label_part(explicit_label)

        if ":" in item:
            name, weights = item.split(":", 1)
            name = normalize_model_name(name)
            weights = weights.strip()
        else:
            name, weights = infer_model_and_weights(item)
        label = explicit_label or build_model_label(name, weights)
        if label in labels:
            raise ValueError(f"Duplicate model output label: {label}")
        labels.add(label)
        specs.append(ModelSpec(name=name, weights=weights, label=label))

    if not specs:
        raise ValueError("At least one model must be provided with --models")
    return tuple(specs)


def parse_csv_tuple(value: Optional[str]) -> Tuple[str, ...]:
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def resolve_devices(device_arg: str) -> List[str]:
    raw = device_arg.strip().lower()
    if not raw:
        raw = "auto"

    if raw == "cpu":
        return ["cpu"]

    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is required for SeisBench device selection") from exc

    cuda_available = torch.cuda.is_available()
    cuda_count = torch.cuda.device_count() if cuda_available else 0

    if raw == "auto":
        return ["cuda:0"] if cuda_available else ["cpu"]
    if raw == "all":
        if not cuda_available:
            return ["cpu"]
        return [f"cuda:{idx}" for idx in range(cuda_count)]
    if raw == "cuda":
        if not cuda_available:
            raise RuntimeError("--device cuda requested, but CUDA is not available")
        return ["cuda:0"]

    devices = [item.strip() for item in raw.split(",") if item.strip()]
    if not devices:
        raise RuntimeError(f"Invalid --device value: {device_arg}")

    for device in devices:
        if device.startswith("cuda"):
            if not cuda_available:
                raise RuntimeError(f"{device} requested, but CUDA is not available")
            if ":" in device:
                index = int(device.split(":", 1)[1])
                if index < 0 or index >= cuda_count:
                    raise RuntimeError(f"{device} requested, but only {cuda_count} CUDA device(s) exist")
    return devices


def distribute_workers(devices: Sequence[str], total_workers: Optional[int]) -> Dict[str, int]:
    if total_workers is None:
        total_workers = len(devices) if len(devices) > 1 else 1
    if total_workers < 1:
        raise ValueError("--workers must be >= 1")

    allocation = {device: 0 for device in devices}
    for index in range(total_workers):
        allocation[devices[index % len(devices)]] += 1
    return allocation


def init_worker(config: RuntimeConfig, model_specs: Tuple[ModelSpec, ...], device: str) -> None:
    global _WORKER_CONFIG, _WORKER_MODELS, _WORKER_DEVICE
    _WORKER_CONFIG = config
    _WORKER_DEVICE = device
    _WORKER_MODELS = load_models(model_specs, device, config)


def load_models(
    model_specs: Tuple[ModelSpec, ...], device: str, config: RuntimeConfig
) -> Dict[str, Tuple[ModelSpec, object]]:
    try:
        import seisbench.models as sbm
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "Missing SeisBench runtime dependency. Install seisbench, obspy, and torch "
            "in the environment used to run this script."
        ) from exc

    if config.torch_threads:
        torch.set_num_threads(config.torch_threads)

    if device.startswith("cuda"):
        torch.cuda.set_device(int(device.split(":", 1)[1]))

    models: Dict[str, Tuple[ModelSpec, object]] = {}
    for spec in model_specs:
        if not hasattr(sbm, spec.name):
            raise RuntimeError(f"seisbench.models has no model named {spec.name}")
        model_class = getattr(sbm, spec.name)
        model = model_class.from_pretrained(spec.weights)
        if config.model_sampling_rate is not None and hasattr(model, "sampling_rate"):
            model.sampling_rate = config.model_sampling_rate
        if hasattr(model, "to"):
            model.to(device)
        if hasattr(model, "eval"):
            model.eval()
        models[spec.label] = (spec, model)
    return models


def station_channels(station: Station, config: RuntimeConfig) -> Tuple[str, ...]:
    if config.exact_channels:
        return config.exact_channels
    if station.channels:
        return station.channels

    prefix = station.channel[:-1] if station.channel else ""
    if not prefix:
        return config.component_suffixes
    return tuple(prefix + suffix for suffix in config.component_suffixes)


def render_waveform_paths(station: Station, date_label: str, channel: str, config: RuntimeConfig) -> List[Path]:
    rendered = config.file_template.format(
        date=date_label,
        net=station.net,
        station=station.sta,
        sta=station.sta,
        channel=channel,
    )
    rendered_path = Path(rendered).expanduser()
    if rendered_path.is_absolute():
        pattern = str(rendered_path)
    else:
        pattern = str(Path(config.data_dir) / rendered_path)

    if any(char in pattern for char in "*?["):
        return [Path(match) for match in sorted(glob.glob(pattern))]

    path = Path(pattern)
    return [path] if path.exists() else []


def read_station_stream(station: Station, date_label: str, config: RuntimeConfig):
    import numpy as np
    import obspy
    from obspy import UTCDateTime

    stream = obspy.Stream()
    missing = []
    for channel in station_channels(station, config):
        paths = render_waveform_paths(station, date_label, channel, config)
        if not paths:
            missing.append(channel)
            continue
        for path in paths:
            stream += obspy.read(str(path))

    if len(stream) < config.min_components:
        return None, missing

    window_start = UTCDateTime(datetime.strptime(date_label, "%Y%m%d")) + config.start_second
    window_end = window_start + config.duration_seconds

    stream.merge(method=1, fill_value="interpolate")
    stream.trim(starttime=window_start, endtime=window_end, pad=False)

    for trace in list(stream):
        if trace.stats.npts == 0:
            stream.remove(trace)
            continue
        if not np.isfinite(trace.data).all():
            stream.remove(trace)

    if len(stream) < config.min_components:
        return None, missing

    if config.detrend:
        stream.detrend("demean")
        stream.detrend("linear")

    if config.freqmin is not None and config.freqmax is not None:
        stream.filter("bandpass", freqmin=config.freqmin, freqmax=config.freqmax, zerophase=True)
    elif config.freqmin is not None:
        stream.filter("highpass", freq=config.freqmin, zerophase=True)
    elif config.freqmax is not None:
        stream.filter("lowpass", freq=config.freqmax, zerophase=True)

    if config.taper > 0:
        stream.taper(max_percentage=config.taper)

    if config.resample_rate is not None:
        stream.interpolate(sampling_rate=config.resample_rate, starttime=window_start)

    return stream, missing


def classify_kwargs(model_name: str, config: RuntimeConfig) -> Dict[str, object]:
    default_p, default_s = DEFAULT_THRESHOLDS.get(model_name, (0.3, 0.3))
    kwargs: Dict[str, object] = {
        "P_threshold": config.p_threshold if config.p_threshold is not None else default_p,
        "S_threshold": config.s_threshold if config.s_threshold is not None else default_s,
        "batch_size": config.batch_size,
    }
    if config.detection_threshold is not None:
        kwargs["detection_threshold"] = config.detection_threshold
    return kwargs


def filter_kwargs_for_callable(func, kwargs: Dict[str, object]) -> Dict[str, object]:
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return kwargs

    parameters = signature.parameters
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    if accepts_kwargs:
        return kwargs
    return {key: value for key, value in kwargs.items() if key in parameters}


def classify_stream(model, model_name: str, stream, config: RuntimeConfig, day_start):
    if config.segment_seconds > 0:
        results = []
        segment_start = day_start
        day_end = day_start + config.duration_seconds
        while segment_start < day_end:
            segment_end = min(segment_start + config.segment_seconds, day_end)
            segment = stream.copy().trim(starttime=segment_start, endtime=segment_end, pad=False)
            if len(segment) > 0:
                kwargs = filter_kwargs_for_callable(model.classify, classify_kwargs(model_name, config))
                results.append(model.classify(segment, **kwargs))
            segment_start = segment_end
        return results

    kwargs = filter_kwargs_for_callable(model.classify, classify_kwargs(model_name, config))
    return [model.classify(stream, **kwargs)]


def to_utcdatetime(value):
    from obspy import UTCDateTime

    if value is None:
        return None
    if isinstance(value, UTCDateTime):
        return value
    return UTCDateTime(value)


def result_pick_records(results, spec: ModelSpec, day_start, station: Station, config: RuntimeConfig):
    records = []
    for result in results:
        picks = getattr(result, "picks", [])
        creator = getattr(result, "creator", spec.label)
        for pick in picks:
            phase = str(getattr(pick, "phase", "")).upper()
            if phase.startswith("P"):
                phase = "P"
            elif phase.startswith("S"):
                phase = "S"
            else:
                continue

            pick_time = to_utcdatetime(getattr(pick, "peak_time", None))
            if pick_time is None:
                pick_time = to_utcdatetime(getattr(pick, "start_time", None))
            if pick_time is None:
                continue

            seconds = float(pick_time - day_start)
            if seconds < config.start_second - 1 or seconds > config.start_second + config.duration_seconds + 1:
                continue

            probability = getattr(pick, "peak_value", 0.0)
            try:
                probability = float(probability)
            except (TypeError, ValueError):
                probability = 0.0

            start_time = to_utcdatetime(getattr(pick, "start_time", None))
            records.append(
                {
                    "model": str(creator),
                    "model_name": spec.name,
                    "model_weights": spec.weights,
                    "model_label": spec.label,
                    "trace_id": str(getattr(pick, "trace_id", f"{station.net}.{station.sta}")),
                    "start_time": start_time.isoformat() if start_time is not None else "",
                    "phase": phase,
                    "pick_time": pick_time.isoformat(),
                    "seconds": seconds,
                    "probability": probability,
                    "amplitude": config.default_amplitude,
                }
            )
    return records


def write_csv(records: Sequence[Dict[str, object]], station: Station, date_label: str, spec: ModelSpec, config: RuntimeConfig) -> None:
    if not config.save_csv:
        return

    csv_dir = Path(config.results_dir) / spec.label / date_label / f"{station.net}.{station.sta}"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / "picking_result.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Model",
                "Model_name",
                "Model_weights",
                "Model_label",
                "Trace_id",
                "Start_time",
                "Phase",
                "Pick_time",
                "Pick_probability",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "Model": record["model"],
                    "Model_name": record["model_name"],
                    "Model_weights": record["model_weights"],
                    "Model_label": record["model_label"],
                    "Trace_id": record["trace_id"],
                    "Start_time": record["start_time"],
                    "Phase": record["phase"],
                    "Pick_time": record["pick_time"],
                    "Pick_probability": record["probability"],
                }
            )


def write_real_files(records: Sequence[Dict[str, object]], station: Station, date_label: str, spec: ModelSpec, config: RuntimeConfig) -> None:
    date_dir = Path(config.output_dir) / spec.label / date_label
    date_dir.mkdir(parents=True, exist_ok=True)

    for phase in ("P", "S"):
        phase_records = sorted(
            (record for record in records if record["phase"] == phase),
            key=lambda record: float(record["seconds"]),
        )
        output_path = date_dir / f"{station.net}.{station.sta}.{phase}.txt"
        with output_path.open("w") as f:
            for record in phase_records:
                f.write(
                    f"{float(record['seconds']):.4f} "
                    f"{float(record['probability']):.4f} "
                    f"{float(record['amplitude']):.4e}\n"
                )


def process_station_day(station: Station, date_label: str) -> Dict[str, object]:
    if _WORKER_CONFIG is None:
        raise RuntimeError("Worker was not initialized")

    config = _WORKER_CONFIG
    try:
        from obspy import UTCDateTime

        stream, missing = read_station_stream(station, date_label, config)
        if stream is None:
            return {
                "status": "skipped",
                "station": f"{station.net}.{station.sta}",
                "date": date_label,
                "picks": 0,
                "message": f"missing components: {','.join(missing)}",
            }

        day_start = UTCDateTime(datetime.strptime(date_label, "%Y%m%d"))
        window_start = day_start + config.start_second
        per_model_counts = {}

        for model_label, (spec, model) in _WORKER_MODELS.items():
            results = classify_stream(model, spec.name, stream.copy(), config, window_start)
            records = result_pick_records(results, spec, day_start, station, config)
            per_model_counts[model_label] = len(records)
            write_csv(records, station, date_label, spec, config)
            write_real_files(records, station, date_label, spec, config)

        return {
            "status": "ok",
            "station": f"{station.net}.{station.sta}",
            "date": date_label,
            "picks": sum(per_model_counts.values()),
            "per_model_counts": per_model_counts,
            "device": _WORKER_DEVICE,
        }
    except Exception:
        return {
            "status": "error",
            "station": f"{station.net}.{station.sta}",
            "date": date_label,
            "picks": 0,
            "message": traceback.format_exc(),
        }


def clean_output_dirs(
    dates: Sequence[str],
    output_dir: Path,
    results_dir: Path,
    model_specs: Sequence[ModelSpec],
    save_csv: bool,
) -> None:
    for spec in model_specs:
        for date_label in dates:
            pick_dir = output_dir / spec.label / date_label
            if pick_dir.exists():
                shutil.rmtree(pick_dir)
            if save_csv:
                result_dir = results_dir / spec.label / date_label
                if result_dir.exists():
                    shutil.rmtree(result_dir)


def progress_iter(futures: Sequence[object]):
    try:
        from tqdm import tqdm

        return tqdm(as_completed(futures), total=len(futures))
    except ImportError:
        return as_completed(futures)


def run_sequential(
    tasks: Sequence[Tuple[Station, str]],
    config: RuntimeConfig,
    model_specs: Tuple[ModelSpec, ...],
    device: str,
) -> List[Dict[str, object]]:
    init_worker(config, model_specs, device)
    results = []
    iterator: Iterable[Tuple[Station, str]]
    try:
        from tqdm import tqdm

        iterator = tqdm(tasks)
    except ImportError:
        iterator = tasks
    for station, date_label in iterator:
        results.append(process_station_day(station, date_label))
    return results


def run_parallel(
    tasks: Sequence[Tuple[Station, str]],
    config: RuntimeConfig,
    model_specs: Tuple[ModelSpec, ...],
    worker_allocation: Dict[str, int],
) -> List[Dict[str, object]]:
    use_spawn = any(device.startswith("cuda") for device in worker_allocation)
    mp_context = multiprocessing.get_context("spawn") if use_spawn else None

    executors = []
    futures = []
    device_cycle = []
    for device, worker_count in worker_allocation.items():
        if worker_count < 1:
            continue
        executor_kwargs = {
            "max_workers": worker_count,
            "initializer": init_worker,
            "initargs": (config, model_specs, device),
        }
        if mp_context is not None:
            executor_kwargs["mp_context"] = mp_context
        executor = ProcessPoolExecutor(**executor_kwargs)
        executors.append(executor)
        device_cycle.append((device, executor))

    try:
        for index, task in enumerate(tasks):
            _, executor = device_cycle[index % len(device_cycle)]
            futures.append(executor.submit(process_station_day, *task))

        results = []
        for future in progress_iter(futures):
            results.append(future.result())
        return results
    finally:
        for executor in executors:
            executor.shutdown(wait=True)


def print_summary(results: Sequence[Dict[str, object]]) -> None:
    ok = sum(1 for result in results if result["status"] == "ok")
    skipped = sum(1 for result in results if result["status"] == "skipped")
    errors = [result for result in results if result["status"] == "error"]
    total_picks = sum(int(result.get("picks", 0)) for result in results)

    print("\nSeisBench picking summary")
    print(f"  processed: {ok}")
    print(f"  skipped:   {skipped}")
    print(f"  errors:    {len(errors)}")
    print(f"  picks:     {total_picks}")

    if skipped:
        print("\nSkipped station/day examples:")
        for result in [item for item in results if item["status"] == "skipped"][:10]:
            print(f"  {result['date']} {result['station']}: {result.get('message', '')}")

    if errors:
        print("\nErrors:")
        for result in errors[:10]:
            print(f"  {result['date']} {result['station']}")
            print(result.get("message", "").rstrip())


def main() -> int:
    args = parse_args()
    station_file = resolve_station_file(args.station_file)
    dates = build_dates(args.start_date, args.nday, args.end_date)
    stations = load_stations(station_file)
    model_specs = parse_models(args.models)
    devices = resolve_devices(args.device)
    worker_allocation = distribute_workers(devices, args.workers)

    config = RuntimeConfig(
        data_dir=str(Path(args.data_dir).expanduser().resolve()),
        output_dir=str(Path(args.output_dir).expanduser().resolve()),
        results_dir=str(Path(args.results_dir).expanduser().resolve()),
        file_template=args.file_template,
        component_suffixes=parse_csv_tuple(args.component_suffixes),
        exact_channels=parse_csv_tuple(args.channels),
        min_components=args.min_components,
        detrend=not args.no_detrend,
        taper=args.taper,
        freqmin=args.freqmin,
        freqmax=args.freqmax,
        resample_rate=args.resample_rate,
        model_sampling_rate=args.model_sampling_rate,
        start_second=args.start_second,
        duration_seconds=args.duration_seconds,
        batch_size=args.batch_size,
        p_threshold=args.p_threshold,
        s_threshold=args.s_threshold,
        detection_threshold=args.detection_threshold,
        segment_seconds=args.segment_seconds,
        default_amplitude=args.default_amplitude,
        save_csv=args.save_csv and not args.no_save_csv,
        torch_threads=args.torch_threads,
    )

    if not stations:
        raise RuntimeError(f"No stations loaded from {station_file}")

    tasks = [(station, date_label) for date_label in dates for station in stations]

    print("SeisBench LOC-FLOW picker")
    print(f"  station file: {station_file}")
    print(f"  waveform dir: {config.data_dir}")
    print(f"  dates:        {', '.join(dates)}")
    print(f"  stations:     {len(stations)}")
    print(f"  models:       {', '.join(f'{spec.name}:{spec.weights} -> {spec.label}' for spec in model_specs)}")
    print(f"  devices:      {', '.join(devices)}")
    print(
        "  workers:      "
        + ", ".join(f"{device}={count}" for device, count in worker_allocation.items())
    )
    print(f"  pick output:  {config.output_dir}/<model_label>/<date>")
    print(f"  CSV results:  {'enabled' if config.save_csv else 'disabled'}")

    if args.dry_run:
        return 0

    if not args.no_overwrite:
        clean_output_dirs(
            dates,
            Path(config.output_dir),
            Path(config.results_dir),
            model_specs,
            config.save_csv,
        )

    total_workers = sum(worker_allocation.values())
    if total_workers == 1:
        results = run_sequential(tasks, config, model_specs, devices[0])
    else:
        results = run_parallel(tasks, config, model_specs, worker_allocation)

    print_summary(results)
    return 1 if any(result["status"] == "error" for result in results) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        raise SystemExit(130)
