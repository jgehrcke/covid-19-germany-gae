# MIT License

# Copyright (c) 2020 - 2021 Dr. Jan-Philip Gehrcke -- https://gehrcke.de

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
Generate "7-Tage-Inzidenz" data files.

7-day incidence (7di): sum of newly confirmed cases within the last seven days,
per 100.000 inhabitants.

This module is part of https://github.com/jgehrcke/covid-19-germany-gae
"""

import argparse
import logging
import os
import json
import sys

import pandas as pd

_tools_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_tools_dir, ".."))

import lib.tsmath
import lib.io

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


DE_AGS_POP_JSON_PATH = os.path.join(_tools_dir, "..", "ags.json")

log.debug("read %s", DE_AGS_POP_JSON_PATH)
with open(DE_AGS_POP_JSON_PATH, "rb") as f:
    AGS_PROPERTY_DICT = json.loads(f.read().decode("utf-8"))

# Get total population (GER): skip AGSs that do not have the populuation
# key set (expected for AGS 3152 "LK Göttingen (alt)". Minus the total for
# Berlin, because Berlin is represented twice, on purpose.
TOTAL_POPULATION_GER = (
    sum(v["population"] for k, v in AGS_PROPERTY_DICT.items() if "population" in v)
    - AGS_PROPERTY_DICT["11000"]["population"]
)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cases_timeseries_csv_path", metavar="cases-timeseries-csv-path"
    )
    parser.add_argument("output_csv_path", metavar="output-csv-path")

    args = parser.parse_args()

    # Supposed to be a CSV file where each column is a 'covid 19 case count'
    # time series.
    df = lib.io.parse_csv_timeseries(args.cases_timeseries_csv_path)

    # Mutate dataframe.
    calc_7_day_incidence_for_each_column(df)

    # Copy df, and drop original columns.
    df_output = df.copy().drop(columns=[c for c in df if not c.endswith("_7di")])

    # First row is expected to contain NaNs (as of building derivative in
    # lib.tsmath.build_daily_change_rate_rolling_window). Drop.
    df_output = df_output.dropna()

    # cosmetical change: rename `sum_cases_7di`, because this can get a more
    # expressive name now.
    df_output = df_output.rename(columns={"sum_cases_7di": "germany_7di"})

    log.info("output df:\n%s", df_output)

    lib.io.write_csv_timeseries(df_output, args.output_csv_path, float_format="%.2f")


def calc_7_day_incidence_for_each_column(df):
    """
    Mutate `df`.

    Assume that each column is a 'covid 19 case count' time series.

    For each column in input Dataframe, add another column with the 7-day
    incidence time series.
    """

    # Assume each column name to be an Amtlicher Gemeindeschluessel (AGS),
    # identifying a county (Landkreis), except for a sum_ column.
    for cname in df:
        series_7di = calc_7_day_incidence_for_column(df, cname)
        # For each column in DF, add another column with the "7 Tage Inzidenz"
        df[f"{cname}_7di"] = series_7di


def calc_7_day_incidence_for_column(df, column):
    window_width_days = 7

    log.info("build seven-day-rolling-window for column %s", column)

    daily_change_rw = lib.tsmath.build_daily_change_rate_rolling_window(
        df=df,
        column=column,
        window_width_days=window_width_days,
        sum_over_time_window=True,
    )

    latest_timestamp = pd.to_datetime(str(daily_change_rw.index.values[-1]))
    latest_timestamp_day_string = latest_timestamp.strftime("%Y-%m-%d %H:%M")

    log.info("last data point time: %s", latest_timestamp_day_string)

    log.info(
        "last data point (absolute count, mean over last %s days): %s",
        window_width_days,
        int(daily_change_rw.iloc[-1] / window_width_days),
    )

    if column.startswith("sum_"):
        pop = TOTAL_POPULATION_GER
    else:
        # Rely on column name to be an Amtlicher Gemeindeschluessel (AGS)
        pop = AGS_PROPERTY_DICT[column]["population"]

    log.info("normalize by population (1/100000 inhabitants), pop count: %s", pop)
    daily_change_norm_rw = daily_change_rw / float(pop) * 100000.0
    log.info(
        "last data point (normalized on pop, sum over last %s days): %s",
        window_width_days,
        int(daily_change_norm_rw.iloc[-1]),
    )

    return daily_change_norm_rw
    # df[f"{column}_7di"] = norm_change_rolling_window
    # print(df[f"{column}_7di"])
    # sys.exit()


if __name__ == "__main__":
    main()
