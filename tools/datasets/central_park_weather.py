# /// script
# requires-python = "==3.14.2"
# dependencies = []
# ///
"""Builds the tested pipeline lab's weather file from NOAA's GHCN-Daily: August 2025 at New
York's Central Park, station USW00094728, as NCEI's Access Data Service gives it.

The file is the service's answer as it is, in tenths of a millimetre, a degree Celsius and a
metre a second, with each value's measurement, quality and source flags and its time of
observation. NCEI updates GHCN-Daily as new reports and checks arrive, so a later answer can
differ; this one was fetched on 25 October 2026, from version 3.35-upd-2026102317.

    uv run tools/datasets/central_park_weather.py <path to write>
"""

import hashlib
import sys
import urllib.request

SOURCE = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations=USW00094728&startDate=2025-08-01&endDate=2025-08-31"
    "&dataTypes=PRCP,SNOW,TMAX,TMIN,AWND,WT01,WT03,WT08&includeAttributes=true&format=csv"
)
# The answer as fetched on 25 October 2026. A different answer stops the build.
SHA256 = "1e099309bf3f2091543867cf6d7a6e88f3d0d9382716f8307654135267495177"


def main(out: str) -> None:
    answer = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(answer).hexdigest()
    if found != SHA256:
        raise SystemExit(f"NCEI's answer has changed: sha256 {found}, expected {SHA256}.")
    with open(out, "wb") as file:
        file.write(answer)


if __name__ == "__main__":
    main(sys.argv[1])
