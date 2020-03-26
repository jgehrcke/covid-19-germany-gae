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
"""

import os
import json
import io
import logging
import sys
import pytz
from datetime import datetime

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
ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


with open(os.path.join(os.path.dirname(__file__), "lk-ags-to-bl.json"), "rb") as f:
    AGS_BL_MAP = json.loads(f.read().decode("utf-8"))


def main():

    # Dataframe with one column per AGS (Landkreis, kreisfreie Stadt)
    df_by_lk = fetch_and_clean_data()
    df_by_bl = aggregate_by_bland(df_by_lk)

    log.info("build sum for each sample")
    df_by_bl["sum_cases"] = df_by_bl.sum(axis=1)
    df_by_lk["sum_cases"] = df_by_lk.sum(axis=1)

    # df = pd.read_csv(io.StringIO(resp.text), index_col=["time_iso8601"])
    # new_row_df.index.name = "time_iso8601"

    log.info("Turn DatetimeIndex into index of ISO 8601 strings")

    # CPython 3.7 for the %z format specifier behavior.
    df_by_bl.index = df_by_bl.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_bl.index.name = "time_iso8601"
    print(df_by_bl)

    df_by_lk.index = df_by_lk.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_lk.index.name = "time_iso8601"
    print(df_by_lk)

    csv_filepath_bk = "data-rl-crowdsource-by-state.csv"
    log.info("write data to CSV file %s", csv_filepath_bk)
    with open(csv_filepath_bk, "wb") as f:
        f.write(df_by_bl.to_csv().encode("utf-8"))

    csv_filepath_lk = "data-rl-crowdsource-by-ags.csv"
    log.info("write data to CSV file %s", csv_filepath_lk)
    with open(csv_filepath_lk, "wb") as f:
        f.write(df_by_lk.to_csv().encode("utf-8"))

    log.info("done")


def aggregate_by_bland(df_by_lk):
    """
    Args:
        df_by_lk: Dataframe with one column per AGS and DatetimeIndex.
            AGS is amtlicher Gemeindeschluessel (of type int), referring to
            a specific Landkreis (LK)/kreisfreie Stadt.

    Returns:
        df_by_bl: Dataframe with one column per Bundesland (BL) and
            DatetimeIndex. The sum of all LKs in the BL. Each column name
            is the ISO 3166 notation for the individual BL, e.g. DE-BY for
            Bavaria.
    """
    log.info("aggregate rl data by bundesland")

    df_by_bl = pd.DataFrame()
    for cname in df_by_lk:
        bland_iso = STATE_NAME_ISONAME_MAP[AGS_BL_MAP[str(cname)]]
        if bland_iso not in df_by_bl:
            df_by_bl[bland_iso] = df_by_lk[cname]
        else:
            df_by_bl[bland_iso] += df_by_lk[cname]

    return df_by_bl


def fetch_and_clean_data():
    log.info("fetch risklayer data from gsheets")
    # risklayer history as CSV from google sheets
    csv = requests.get(os.environ["RISKLAYER_HISTORY_CSV_URL"]).text
    df = pd.read_csv(io.StringIO(csv))

    log.info("parse rk data and normalize")
    # Drop text info, keep using AGS (amtlicher Gemeindeschluessel).
    df.drop(["GEN"], axis=1, inplace=True)

    # AGS data seems to be pretty clean, no need to fillna.
    # df["AGS"] = df["AGS"].fillna(0.0).astype("int")

    df["AGS"] = df["AGS"].astype("int")
    df = df.set_index("AGS")

    # Set new column names, including hour of the day and the Germany
    # timezone set for each day, as ISO 8601 string.
    # Column names so far are strings representing points in time. Specific dates
    # (resolution: day), and "current". Normalize this to time strings with
    # 1 hour resolution, towards transposing the DF, towards a DF with a
    # DatetimeIndex.
    rename_map = {}
    for cname in df:
        if cname == "current":
            # Set the current hour of the day as ISO 8601 string including the
            # tz info for _current_ Germany (subjet to daylight switch, not
            # that it matters too much, but yeah..). Example:
            # '2020-03-26T18:00:00+0100'
            rename_map["current"] = datetime.strftime(
                datetime.now(tz=pytz.timezone("Europe/Amsterdam")),
                "%Y-%m-%dT%H:00:00%z",
            )
            continue
        # Sanity-check input data, raises ValueError upon unexpected data.
        try:
            datetime.strptime(cname, "%d.%m.%Y")
        except ValueError:
            # There is the special case of `11.03.2020.1`, which seems to represent
            # some later point in time. Assume just a couple of hours.
            if cname == "11.03.2020.1":
                rename_map[cname] = f"2020-03-11T10:00:00+0100"
                continue
            raise
        # The risklayer crowd does heavy work in their evening, mapping the result
        # to the _next day_. Example: late in the evening, towards midnight between
        # March 25 and March 26 they settle on the value that they then publish as
        # March 26. That is, set an _early_ hour of the day.
        sample_time_naive = datetime.strptime(f"{cname} 01:00:00", "%d.%m.%Y %H:%M:%S")
        # This only _sets_ tz info, does not do number conversion (super easy
        # to reason about).
        sample_time_aware = pytz.timezone("Europe/Amsterdam").localize(
            sample_time_naive
        )
        sample_time_aware_iso8601 = datetime.strftime(
            sample_time_aware, "%Y-%m-%dT%H:00:00%z",
        )

        rename_map[cname] = sample_time_aware_iso8601

    # Now use the rename map to actually rename the columns in the dataframe.
    df = df.rename(columns=rename_map)

    log.info("transpose rl data")

    df = df.transpose()
    # df.index = pd.to_datetime(df.index, format="%d.%m.%Y %H:%M:%S")
    df.index = pd.to_datetime(df.index)
    df.index.rename("time", inplace=True)
    print(df.index)
    return df


if __name__ == "__main__":
    main()
