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
This program is part of https://github.com/jgehrcke/covid-19-germany-gae

Columns in output CSV file:

    ags: amtlicher Gemeindeschlüssel for county. See ags.json.
    county_name: name of the county (Landkreis).
    state_name: name of the state (Bundesland).
    population: population count for county.
    rl_cases_total: current total case count, from Risklayer GmbH (RL) data set.
    rl_cases_7di: current 7-day incidence (7di) value (RL data set).
    rl_deaths_total: current total death count (RL data set).
    rki_cases_total: current total case count, from Robert Koch-Institut data set.
    rki_cases_7di: current 7-day incidence (7di) value (RKI data set).
    rki_deaths_total: current total death count (RKI data set).

Example program for parsing the output CSV file, including its meta data:


    import json
    import pandas

    # Parse CSV file, ignore first line.
    print(pandas.read_csv("more-data/latest-aggregate.csv", comment="#"))

    # Read first line and JSON-decode meta data.
    with open("more-data/latest-aggregate.csv", "rb") as f:
        firstline = f.readline().decode("utf-8")
        metadata = json.loads(firstline.strip("#"))

    print(metadata)


The state/version of individual data points is annotated in the header
of the output CSV file (valid JSON doc after '#'):

    # {"time_iso8601_last_update_rki": "2021-01-16T17:00:00+0000", "time_iso8601_last_update_rl": "2021-01-18T01:00:00+0000"}
    ags,county_name,state,population,rl_cases_total,rl_cases_7di,rl_deaths_total,rki_cases_total,rki_cases_7di,rki_deaths_total
    1001,SK Flensburg,Schleswig-Holstein,90164,763,133,12,745,136,11
    ...


Note that these two timestamps typically differ! That is, not all the numbers
in the output file represent the same "current" state.

Output data structure example (string representation):

                       county_name               state  population  ...  rki_cases_total  rki_cases_7di  rki_deaths_total
    ags                                                             ...
    1001              SK Flensburg  Schleswig-Holstein       90164  ...              745            136                11
    1002                   SK Kiel  Schleswig-Holstein      246794  ...             2736             67                52
    1003                 SK Lübeck  Schleswig-Holstein      216530  ...             3102            107                30
    1004             SK Neumünster  Schleswig-Holstein       80196  ...              848            111                14
    1051           LK Dithmarschen  Schleswig-Holstein      133193  ...             1122             64                33
    ...                        ...                 ...         ...  ...              ...            ...               ...
    16073   LK Saalfeld-Rudolstadt           Thüringen      103199  ...             3450            504               110
    16074  LK Saale-Holzland-Kreis           Thüringen       82950  ...             2183            324                45
    16075      LK Saale-Orla-Kreis           Thüringen       80312  ...             2740            270                59
    16076                 LK Greiz           Thüringen       97398  ...             2956            254                96
    16077      LK Altenburger Land           Thüringen       89393  ...             3877            487                77

    [413 rows x 9 columns]



Note that in the output CSV file, some fields may be empty, namely
the RL data fields for individual Berlin districts. Example snippet:


    11000,Berlin,Berlin,3669491,112516,173,1833,112262,168,1823
    11001,SK Berlin Mitte,Berlin,380917,,,,14457,142,173
    11002,SK Berlin Friedrichshain-Kreuzberg,Berlin,290083,,,,9888,118,89
    11003,SK Berlin Pankow,Berlin,409454,,,,9296,185,96
    11004,SK Berlin Charlottenburg-Wilmersdorf,Berlin,342950,,,,9566,145,170
    11005,SK Berlin Spandau,Berlin,244458,,,,8528,202,141
    11006,SK Berlin Steglitz-Zehlendorf,Berlin,308582,,,,8287,160,117
    11007,SK Berlin Tempelhof-Schöneberg,Berlin,351062,,,,11525,170,292
    11008,SK Berlin Neukölln,Berlin,328666,,,,13475,157,251
    11009,SK Berlin Treptow-Köpenick,Berlin,273817,,,,5764,177,87
    11010,SK Berlin Marzahn-Hellersdorf,Berlin,271311,,,,6080,166,99
    11011,SK Berlin Lichtenberg,Berlin,294937,,,,6609,188,124
    11012,SK Berlin Reinickendorf,Berlin,266219,,,,8787,159,184
    12051,SK Brandenburg a.d.Havel,Brandenburg,72184,1153,168,34,1098,181,29
    12052,SK Cottbus,Brandenburg,99678,3545,261,120,2013,205,75
    12053,SK Frankfurt (Oder),Brandenburg,57751,1212,127,45,1192,131,43
    12054,SK Potsdam,Brandenburg,180334,4529,231,144,3847,316,129
"""

import argparse
import os
import json
import sys

import pandas as pd


_main_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _main_dir)
import lib


log = lib.init_logger()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_csv_path", metavar="output-csv-path")

    # df_rki_7di = lib.io.parse_csv_timeseries(
    #     os.path.join(_main_dir, "more-data", "7di-rki-by-ags.csv")
    # )

    ags_properties = lib.io.read_ags_prop_json()

    df_rki_7di, lts_rki_7di = get_df("more-data", "7di-rki-by-ags.csv")
    df_rl_7di, lts_rl_7di = get_df("more-data", "7di-rl-by-ags.csv")
    df_rki_cases, lts_rki = get_df("cases-rki-by-ags.csv")
    df_rl_cases, lts_rl = get_df("cases-rl-crowdsource-by-ags.csv")
    df_rki_deaths, _ = get_df("deaths-rki-by-ags.csv")
    df_rl_deaths, _ = get_df("deaths-rl-crowdsource-by-ags.csv")

    # The data files above are expected to have been generated at the same
    # time. It is expected that the timestamps of the last data points
    # across these files (for RL, RKI separately) are the same. Verify that.
    assert lts_rki_7di == lts_rki, f"{lts_rki_7di} does not equal {lts_rki}"
    assert lts_rl_7di == lts_rl, f"{lts_rl_7di} does not equal {lts_rl}"

    # Build up data rows for df construction. Rely on CPython's behavior to
    # retain order (of "rows", as they are "inserted").
    rows_for_df = []
    for ags, props in ags_properties.items():

        if ags == '16056':
            log.info("ags: 16056 now reported as 16063, see issue 1748")
            continue

        if props["name"] == "LK Göttingen (alt)":
            # That AGS is in ags.json for legacy reasons, skip processing.
            continue

        rki_cases_total = df_rki_cases[ags].iloc[-1]
        rki_deaths_total = df_rki_deaths[ags].iloc[-1]
        rki_cases_7di = df_rki_7di[f"{ags}_7di"].iloc[-1]

        try:
            rl_cases_total = df_rl_cases[ags].iloc[-1]
            rl_deaths_total = df_rl_deaths[ags].iloc[-1]
            rl_cases_7di = df_rl_7di[f"{ags}_7di"].iloc[-1]
        except KeyError as exc:
            if ags.startswith("110"):
                log.info("expected: RL dataset does not contain AGS %s", ags)
                # Add `NaN` to df. Results in empty field upon CSV export.
                rl_cases_total = None
                rl_deaths_total = None
                rl_cases_7di = None
            else:
                raise exc

        rows_for_df.append(
            {
                "ags": ags,
                "county_name": props["name"],
                "state": props["state"],
                "population": props["population"],
                "rl_cases_total": rl_cases_total,
                "rl_cases_7di": rl_cases_7di,
                "rl_deaths_total": rl_deaths_total,
                "rki_cases_total": rki_cases_total,
                "rki_cases_7di": rki_cases_7di,
                "rki_deaths_total": rki_deaths_total,
            }
        )

    df = pd.DataFrame.from_records(data=rows_for_df, index="ags")
    # print(df)
    # print(df["rl_cases_total"])

    # We could write out all numbers as integers after all, including 7di data
    # (which as of the time of writing is of type float in its csv file):
    # integer precision is sufficient for 7-day incidence data -- the
    # systematic and statistical errors are certainly larger than 1.0. However,
    # as discussed in
    # https://github.com/jgehrcke/covid-19-germany-gae/issues/369 it's nice to
    # have one digit precision, for comparability with other sources. df =
    # df.apply(pd.to_numeric, downcast="integer", errors="ignore") Note that
    # traditionally pandas did not support NaNs in an integer column. But that
    # changed recently, with the Int64 type -- see
    # https://stackoverflow.com/a/54194908/145400
    for c in df.columns:
        if "7di" in c:
            log.info("do not convert 7di column %s to int", c)
            continue

        try:
            df[c] = df[c].astype("Float64").astype("Int64")
        except Exception as e:
            log.info("could not convert column %s to Int64: %s", c, str(e))
            pass

    # print(df)

    metad = {
        "time_iso8601_last_update_rki": lts_rki,
        "time_iso8601_last_update_rl": lts_rl,
    }

    headerline = "# " + json.dumps(metad)

    path = "more-data/latest-aggregate.csv"
    log.info("write latest aggregate state to CSV file %s -- df:\n%s", path, df)
    with open(path, "wb") as f:
        f.write(f"{headerline}\n".encode("utf-8"))
        f.write(df.to_csv(float_format="%.2f").encode("utf-8"))

    log.info("done writing %s", path)


def get_df(*pathelems):
    df = lib.io.parse_csv_timeseries(os.path.join(_main_dir, *pathelems))

    # In a pandas DatetimeIndex, the timezone information (if stored) is stored
    # on the column. That is, the individual timestamp when accessed with e.g.
    # df.index.values[-1] does _not_ contain tz information, it's naive. We
    # know that it's given in UTC, and with `utc=True`, pandas makes the result
    # tz-aware, explicitly annotating the datetime object with tz info for UTC.
    latest_timestamp = pd.to_datetime(df.index.values[-1], utc=True)
    log.info("latest timestamp in file: %s", latest_timestamp)
    latest_timestamp_iso8601 = latest_timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")
    return df, latest_timestamp_iso8601


if __name__ == "__main__":
    main()
