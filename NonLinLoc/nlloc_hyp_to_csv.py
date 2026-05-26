#!/usr/bin/env python3
"""Convert NonLinLoc .hyp summary output to a compact CSV table."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


COLUMNS = [
    "date-time",
    "latitude",
    "longitude",
    "depth",
    "RMS",
    "Nphs",
    "Gap",
    "Dist",
    "errH",
    "errZ",
    "Mamp",
    "Mdur",
    "expect_lat",
    "expect_lon",
    "expect_z",
    "EllipsoidAz1",
    "EllipsoidDip1",
    "EllipsoidLen1",
    "EllipsoidAz2",
    "EllipsoidDip2",
    "EllipsoidLen2",
    "EllipsoidLen3",
    "minHorUnc",
    "maxHorUnc",
    "azMaxHorUnc",
    "pdfVolume",
    "publicId",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert NonLinLoc hyp output to CSV.")
    parser.add_argument("input_hyp")
    parser.add_argument("output_csv")
    return parser.parse_args()


def match(pattern: str, text: str) -> str:
    found = re.search(pattern, text)
    return found.group(1) if found else ""


def parse_event(event_text: str) -> dict[str, str]:
    result: dict[str, str] = {}

    found = re.search(
        r"GEOGRAPHIC\s+OT\s+(\d{4})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+([\d.\-+eE]+)",
        event_text,
    )
    if found:
        result["date-time"] = (
            f"{found.group(1)}-{found.group(2)}-{found.group(3)} "
            f"{found.group(4)}:{found.group(5)}:{found.group(6)}"
        )
    else:
        result["date-time"] = ""

    result["latitude"] = match(r"Lat\s+([\d.\-+eE]+)", event_text)
    result["longitude"] = match(r"Long\s+([\d.\-+eE]+)", event_text)
    result["depth"] = match(r"Depth\s+([\d.\-+eE]+)", event_text)
    result["RMS"] = match(r"RMS\s+([\d.\-+eE]+)", event_text)
    result["Nphs"] = match(r"Nphs\s+(\d+)", event_text)
    result["Gap"] = match(r"Gap\s+([\d.\-+eE]+)", event_text)
    result["Dist"] = match(r"Dist\s+([\d.\-+eE]+)", event_text)
    result["Mamp"] = match(r"Mamp\s+([\d.\-+eE]+)", event_text)
    result["Mdur"] = match(r"Mdur\s+([\d.\-+eE]+)", event_text)
    result["errH"] = match(r"stdErr\s+([\d.\-+eE]+)", event_text)

    zz = match(r"ZZ\s+([\d.\-+eE]+)", event_text)
    if zz:
        try:
            result["errZ"] = f"{math.sqrt(float(zz)):.6f}"
        except ValueError:
            result["errZ"] = ""
    else:
        result["errZ"] = ""

    result["expect_lat"] = match(r"STAT_GEOG\s+.*ExpectLat\s+([\d.\-+eE]+)", event_text)
    result["expect_lon"] = match(r"STAT_GEOG\s+.*Long\s+([\d.\-+eE]+)", event_text)
    result["expect_z"] = match(r"STAT_GEOG\s+.*Depth\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidAz1"] = match(r"EllAz1\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidDip1"] = match(r"Dip1\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidLen1"] = match(r"Len1\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidAz2"] = match(r"Az2\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidDip2"] = match(r"Dip2\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidLen2"] = match(r"Len2\s+([\d.\-+eE]+)", event_text)
    result["EllipsoidLen3"] = match(r"Len3\s+([\d.\-+eE]+)", event_text)
    result["minHorUnc"] = match(r"minHorUnc\s+([\d.\-+eE]+)", event_text)
    result["maxHorUnc"] = match(r"maxHorUnc\s+([\d.\-+eE]+)", event_text)
    result["azMaxHorUnc"] = match(r"azMaxHorUnc\s+([\d.\-+eE]+)", event_text)
    result["pdfVolume"] = match(r"oct_tree_integral\s+([\d.\-+eE]+)", event_text)
    result["publicId"] = match(r"PUBLIC_ID\s+(\S+)", event_text)

    return result


def main() -> None:
    args = parse_args()
    input_file = Path(args.input_hyp)
    output_file = Path(args.output_csv)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    content = input_file.read_text()
    events = [event for event in re.split(r"\n\s*\n", content.strip()) if event.strip()]
    parsed_events = [parse_event(event) for event in events]

    with output_file.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(parsed_events)

    print(f"CSV file has been created at: {output_file}")


if __name__ == "__main__":
    main()
