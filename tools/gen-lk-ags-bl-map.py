# MIT License

# Copyright (c) 2020 Dr. Jan-Philip Gehrcke

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This program is part of https://github.com/jgehrcke/covid-19-germany-gae

Purpose of this tool is to create a JSON file a mapping between "Amtlicher
Gemeindeschlüssel" (AGS) to Bundesland.

https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel

This association is constant, this tool is here for transparency.
"""

import os
import json
import logging
import urllib.parse

import requests


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


def fetch_lks():
    """
    Conduct a synthetic query towards getting the set of Landkreise. It's a
    bit brute-force as this is a time series query, but it queries for a
    small time window only, just to be sure to cover all Landkreise for which
    there is time series data in the ArcGIS system.
    """

    # Trailing `?`.
    AG_RKI_SUMS_QUERY_BASE_URL = os.environ["AG_RKI_SUMS_QUERY_BASE_URL"]

    params = urllib.parse.urlencode(
        {
            "where": "(Meldedatum>timestamp '2020-03-17') AND (Meldedatum<timestamp '2020-03-21')",
            "returnGeometry": "false",
            "outFields": "IdLandkreis, Landkreis, Bundesland",
            "orderByFields": "IdLandkreis asc",
            "resultOffset": 0,
            "resultRecordCount": 10 ** 6,
            "f": "json",
        }
    )
    url = f"{AG_RKI_SUMS_QUERY_BASE_URL}{params}"

    log.info("Query for set of LKs")
    resp = requests.get(url)
    resp.raise_for_status()
    objs = [o["attributes"] for o in resp.json()["features"]]

    # create simple dictionary with AGS (int) as key and per-LK detail as val.
    landkreise = {}
    log.info("got %s feature objects", len(objs))
    for o in objs:
        landkreise[int(o["IdLandkreis"])] = {
            "name": o["Landkreis"],
            "state": o["Bundesland"],
        }

    log.info("constructed %s LK objects", len(landkreise))
    return landkreise


lks = fetch_lks()

# Add a special entry for all of Berlin (as ZEIT ONLINE for example does).
# lks = {ags: l for ags, l in lks.items() if not str(ags).startswith("110")}
lks[11000] = {
    "name": "Berlin",
    "state": "Berlin",
    "note": "represents all of Berlin, includes 110XX",
}

# Sort by ags.
lks = dict(sorted(lks.items()))

log.info("write JSON file with %s AGS entries", len(lks))


# Note that JSON only allows text keys, not numbers.
with open("ags.json", "wb") as f:
    f.write(json.dumps(lks, indent=2, ensure_ascii=False).encode("utf-8"))
