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

import os
import io
import logging
import json
import sys
from time import time
from datetime import datetime

import pandas as pd
import pytz
import requests

STATE_NAME_ISONAME_MAP = {
    "Baden-Württemberg": "DE-BW",
    "Bayern": "DE-BY",
    "Brandenburg": "DE-BB",
    "Berlin": "DE-BE",
    "Bremen": "DE-HB",
    "Hamburg": "DE-HH",
    "Hessen": "DE-HE",
    "Mecklenburg-Vorpommern": "DE-MV",
    "Niedersachsen": "DE-NI",
    "Nordrhein-Westfalen": "DE-NW",
    "Rheinland-Pfalz": "DE-RP",
    "Saarland": "DE-SL",
    "Sachsen-Anhalt": "DE-ST",
    "Sachsen": "DE-SN",
    "Schleswig-Holstein": "DE-SH",
    "Thüringen": "DE-TH",
}
ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)

with open(f"{os.path.dirname(__file__)}/lk-ags-to-bl.json", "rb") as f:
    AGS_BL_MAP = json.loads(f.read().decode("utf-8"))


def main():
    # Get current state snapshot (no history).
    t_source_last_updated, df_current = fetch_current_data_for_each_bundesland_as_df()
    df_previous_csv = fetch_current_csv_as_df()

    log.info("received this data point:")
    print(df_current)

    # Parse iso8601 time string of last CSV row into native datetime object.
    currentdata_last_time = datetime.strptime(
        df_previous_csv.index[-1], "%Y-%m-%dT%H:%M:%S%z"
    )

    # Let a human do sanity checks, but support that human.
    log.info("last timestamp in csv dataset: %s", currentdata_last_time.isoformat())
    log.info("source last updated at: %s", t_source_last_updated.isoformat())
    seconds_newer = (t_source_last_updated - currentdata_last_time).total_seconds()
    hours_newer = seconds_newer / 3600.0

    log.info(
        "source is %.2f hours newer", hours_newer,
    )

    if hours_newer < 0:
        sys.exit("new data is old data? that seems quite wrong, aborting")

    if hours_newer < 12:
        log.info('Replace last sample with more recent data')
        df_previous_csv = df_previous_csv[:-1]

    if hours_newer > 24:
        log.warning("more than a day between the new data point and the last one")

    log.info("add new sample to existing data set")
    df_new = df_previous_csv.append(df_current)

    log.info("new data set:")
    # print(df_new)

    cnames_for_cases = [iname + "_cases" for iname in STATE_NAME_ISONAME_MAP.values()]
    cnames_for_deaths = [iname + "_deaths" for iname in STATE_NAME_ISONAME_MAP.values()]

    df_new["sum_cases"] = df_new[cnames_for_cases].sum(axis=1)
    df_new["sum_deaths"] = df_new[cnames_for_deaths].sum(axis=1)

    # print(df_new["sum_cases"])
    # print(df_new["sum_deaths"])

    new_csv_filepath = "data.csv.new"
    log.info("write new CSV file to %s", new_csv_filepath)
    with open(new_csv_filepath, "wb") as f:
        f.write(df_new.to_csv().encode("utf-8"))

    log.info("done")


def fetch_current_csv_as_df():

    url = "https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/data.csv"
    log.info("fetch csv data from github: %s", url)
    resp = requests.get(url)
    resp.raise_for_status()

    # Using the iso8601 time strings as index has the advantage that individual
    # colunmns (Series objects) are JSON-encode-ready by just doing
    # `Series.to_dict()` yields an ordered map of timestamp:value pairs.
    df = pd.read_csv(io.StringIO(resp.text), index_col=["time_iso8601"])
    return df


def fetch_current_data_for_each_bundesland_as_df():
    def _parse_zo_timestring_into_dt(timestring):
        # This is the third iteration already, as ZO changes their implementation
        # often. They came to reason and now use ISO 8601.
        return datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z")

    # TODO: add retries for robustness
    log.info("fetch current data for each state/bundesland (ZO)")
    url = f"{ZEIT_JSON_URL}?time={time()}"
    jdata = requests.get(url).json()
    t_source_last_updated = _parse_zo_timestring_into_dt(jdata["lastUpdate"])

    agss = [k["ags"] for k in jdata["kreise"]["items"]]
    log.info("got data for %s amtliche Gemeindeschluessel (LKs)", len(agss))

    log.info("assign Gemeindeschluessel to Bundeslaender")
    for kreis in jdata["kreise"]["items"]:
        kreis["bland"] = AGS_BL_MAP[str(kreis["ags"])]

    kreise_for_bland = {}
    for bland in STATE_NAME_ISONAME_MAP:
        log.info("aggregate kreise for %s", bland.upper())
        kreise_for_bland[bland] = [
            k["currentStats"] for k in jdata["kreise"]["items"] if k["bland"] == bland
        ]

    for bland, kreise in kreise_for_bland.items():
        log.info("%s: %s kreis/ags", bland, len(kreise))

    # Now turn this newly obtained snapshot (numbers for all states for a
    # specific point in time) into a pandas DataFrame with n columns and a
    # single row, using the same structure as the DataFrame that is used to
    # construct the CSV in the first place.
    new_row_dict = {"source": "zeit online (gen3)"}
    for bland, kreise in kreise_for_bland.items():
        state_isoname = STATE_NAME_ISONAME_MAP[bland]
        cases = sum(k["count"] for k in kreise)
        deaths = sum(k["dead"] for k in kreise)
        new_row_dict[state_isoname + "_cases"] = [cases]
        new_row_dict[state_isoname + "_deaths"] = [deaths]

    new_row_df = pd.DataFrame(new_row_dict)
    new_row_df.index = [t_source_last_updated.isoformat()]
    new_row_df.index.name = "time_iso8601"

    # print(new_row_df)

    # sys.exit()

    return (t_source_last_updated, new_row_df)


if __name__ == "__main__":
    main()
