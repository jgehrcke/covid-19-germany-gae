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

import io
import logging

from datetime import datetime
import pytz

import pandas as pd
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


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


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
        "source is %.2f hours newer (if that is fishy or negative: don't commit this)",
        hours_newer,
    )

    log.info("add new sample to existing data set")
    df_new = df_previous_csv.append(df_current)

    log.info("new data set:")
    print(df_new)

    cnames_for_cases = [iname + "_cases" for iname in STATE_NAME_ISONAME_MAP.values()]
    cnames_for_deaths = [iname + "_deaths" for iname in STATE_NAME_ISONAME_MAP.values()]

    # df_new["sum_cases"] = df_new[cnames_for_cases].sum(axis=1)
    # df_new["sum_deaths"] = df_new[cnames_for_deaths].sum(axis=1)

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

    # TODO: add retries for robustness
    log.info("fetch current data for each state/bundesland")
    url = "https://interactive.zeit.de/cronjobs/2020/corona/data.json"
    jdata = requests.get(url).json()

    t_source_last_updated = parse_zo_timestring_into_dt(jdata["changeTimestamp"])

    # Now turn this newly obtained snapshot (numbers for all states for a
    # specific point in time) into a pandas DataFrame with n columns and a
    # single row, using the same structure as the DataFrame that is used to
    # construct the CSV in the first place.
    new_row_dict = {"source": "zeit online"}
    for obj in jdata["states"]:
        state_isoname = STATE_NAME_ISONAME_MAP[obj["state"]]
        new_row_dict[state_isoname + "_cases"] = [obj["count"]]
        new_row_dict[state_isoname + "_deaths"] = [obj["dead"]]

    new_row_df = pd.DataFrame(new_row_dict)
    new_row_df.index = [t_source_last_updated.isoformat()]
    new_row_df.index.name = "time_iso8601"

    return (t_source_last_updated, new_row_df)


def parse_zo_timestring_into_dt(timestring):
    # This timestamp is a string of the following format:
    #
    #    '17. März 2020, 21:22 Uhr'
    #
    # This is pretty horrible as an interface, but of course we can work
    # on that, yolo! But let's not plan into the future longer than May.
    # Who would need that, right?
    ts = timestring
    ts = ts.replace("März", "03").replace("April", "04").replace("Mai", "05")
    ts = ts.replace(",", "").replace(".", "")

    t = datetime.strptime(ts, "%d %m %Y %H:%M Uhr")

    # `t` is so far not timezone-aware (no timezone set). Set the
    # Amsterdam/Berlin tz explicitly (which is what the authors of this JSON
    # doc imply).
    t = pytz.timezone("Europe/Amsterdam").localize(t)
    return t


if __name__ == "__main__":
    main()
