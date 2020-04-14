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
import urllib.parse
from datetime import datetime, timedelta
from itertools import zip_longest

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


with open(os.path.join(os.path.dirname(__file__), "..", "ags.json"), "rb") as f:
    AGS_BL_MAP = json.loads(f.read().decode("utf-8"))


def main():

    # Dataframe with one column per AGS (Landkreis, kreisfreie Stadt)
    df_by_lk = fetch_and_clean_data()

    # split deaths into its own dataframe.
    df_by_lk_deaths = pd.concat(
        [df_by_lk[c] for c in df_by_lk if str(c).endswith("_deaths")], axis=1
    )
    df_by_lk_deaths.rename(
        columns={c: int(c.split("_")[0]) for c in df_by_lk_deaths}, inplace=True
    )
    df_by_lk_cases = pd.concat(
        [df_by_lk[c] for c in df_by_lk if "_" not in str(c)], axis=1
    )

    df_by_bl_cases = aggregate_by_bland(df_by_lk_cases)

    df_by_bl_deaths = aggregate_by_bland(df_by_lk_deaths)

    log.info("build sum for each sample")
    df_by_bl_cases["sum_cases"] = df_by_bl_cases.sum(axis=1)
    df_by_bl_deaths["sum_deaths"] = df_by_bl_deaths.sum(axis=1)

    df_by_lk_cases["sum_cases"] = df_by_lk_cases.sum(axis=1)
    df_by_lk_deaths["sum_deaths"] = df_by_lk_deaths.sum(axis=1)

    # df = pd.read_csv(io.StringIO(resp.text), index_col=["time_iso8601"])
    # new_row_df.index.name = "time_iso8601"

    # csv_filepath = "data-rki-by-lk.csv"
    # log.info("write data to CSV file %s", csv_filepath)
    # with open(csv_filepath, "wb") as f:
    #     f.write(df.to_csv().encode("utf-8"))

    # sys.exit()

    log.info("Turn DatetimeIndex into index of ISO 8601 strings")

    # CPython 3.7 for the %z format specifier behavior.
    df_by_bl_cases.index = df_by_bl_cases.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_bl_cases.index.name = "time_iso8601"
    print(df_by_bl_cases)
    csv_filepath_bl_cases = "cases-rki-by-state.csv"
    log.info("write data to CSV file %s", csv_filepath_bl_cases)
    with open(csv_filepath_bl_cases, "wb") as f:
        f.write(df_by_bl_cases.to_csv().encode("utf-8"))

    df_by_bl_deaths.index = df_by_bl_deaths.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_bl_deaths.index.name = "time_iso8601"
    print(df_by_bl_deaths)
    csv_filepath_bl_deaths = "deaths-rki-by-state.csv"
    log.info("write data to CSV file %s", csv_filepath_bl_deaths)
    with open(csv_filepath_bl_deaths, "wb") as f:
        f.write(df_by_bl_deaths.to_csv().encode("utf-8"))

    df_by_lk_cases.index = df_by_lk_cases.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_lk_cases.index.name = "time_iso8601"
    print(df_by_lk_cases)
    csv_filepath_lk_cases = "cases-rki-by-ags.csv"
    log.info("write data to CSV file %s", csv_filepath_lk_cases)
    with open(csv_filepath_lk_cases, "wb") as f:
        f.write(df_by_lk_cases.to_csv().encode("utf-8"))

    df_by_lk_deaths.index = df_by_lk_deaths.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_lk_deaths.index.name = "time_iso8601"
    print(df_by_lk_deaths)
    csv_filepath_lk_deaths = "deaths-rki-by-ags.csv"
    log.info("write data to CSV file %s", csv_filepath_lk_deaths)
    with open(csv_filepath_lk_deaths, "wb") as f:
        f.write(df_by_lk_deaths.to_csv().encode("utf-8"))

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
        ags = str(cname).split("_")[0]
        bland_iso = STATE_NAME_ISONAME_MAP[AGS_BL_MAP[ags]["state"]]
        if bland_iso not in df_by_bl:
            df_by_bl[bland_iso] = df_by_lk[cname]
        else:
            df_by_bl[bland_iso] += df_by_lk[cname]

    return df_by_bl


def fetch_and_clean_data():
    log.info("fetch LK-resolved RKI data from arcgis system")

    # `landkreise` is a dictionary where each item represents a Landkreis or
    # kreisfreie Stadt. Keys are AGS, value has some detail about Landkreis
    # such as Bundesland and LK name.
    landkreise = fetch_lks()

    ags_list_ref = [int(a) for a in AGS_BL_MAP.keys()]
    ags_list_from_rki = [int(a) for a in landkreise.keys()]

    dataframes = []
    for subset in chunks(ags_list_from_rki, 40):
        # The chunker fills the last chunk with Nones.
        agss = [ags for ags in subset if ags is not None]

        # `ndfs` is a dict with AGS as key, and a per-LK dataframe as val.
        ndfs = fetch_history_for_many_ags(agss)

        # I have seen that this can happen. Not quite sure why/now.
        for ags, df in ndfs.items():
            if not len(df):
                log.warning("dataframe empty for ags %s", ags)

        log.info("concatenate non-empty chunk dataframes")
        dfs_chunk = [df for _, df in ndfs.items() if len(df)]

        if not dfs_chunk:
            log.warning("no non-empty chunk dataframes, skip chunk")
            continue

        log.info("build chunk df from %s non-empty dfs", len(dfs_chunk))
        dataframes.append(pd.concat(dfs_chunk, axis=1))

    log.info("concatenate chunk dataframes")
    df_all_agss = pd.concat(dataframes, axis=1)
    print(df_all_agss)

    missed = set(ags_list_from_rki) - set([c for c in df_all_agss])
    if len(missed):
        log.error("missing data for these ags: %s", missed)

    lacking_wrt_ref = set(ags_list_ref) - set([c for c in df_all_agss])
    log.info("missing AGS compared to ref AGS list: %s", lacking_wrt_ref)

    # The reference set has one AGS for entire Berlin -> what follows is
    # expected.
    assert lacking_wrt_ref == set([11000])

    added_wrt_ref = set([c for c in df_all_agss]) - set(ags_list_ref)
    log.info("on top of ref AGS list: %s", added_wrt_ref)

    # Give Berlin some special treatment. Aggregate.
    # Create view from big DF with Berlin AGSs.
    df_berlin = df_all_agss[[c for c in df_all_agss if str(c).startswith("110")]]

    # split deaths for Berlin into its own dataframe.
    df_berlin_deaths = pd.concat(
        [df_berlin[c] for c in df_berlin if str(c).endswith("_deaths")], axis=1
    )
    df_berlin_deaths.rename(
        columns={c: int(str(c).split("_")[0]) for c in df_berlin}, inplace=True
    )
    df_berlin_cases = pd.concat(
        [df_berlin[c] for c in df_berlin if "_" not in str(c)], axis=1
    )

    log.info("berlin cases:\n%s", df_berlin_cases)
    log.info("berlin deaths:\n%s", df_berlin_deaths)
    # If there's any NaN in a row then keep the NaN sum (otherwise even if all
    # values along a row are NaNs the sum would be 0.0)
    df_berlin_cases_sum = df_berlin_cases.sum(axis=1, skipna=False)
    df_berlin_deaths_sum = df_berlin_deaths.sum(axis=1, skipna=False)
    print(df_berlin_cases_sum)
    print(df_berlin_deaths_sum)

    # "Final" dataframe, with one column for all of Berlin.
    df = df_all_agss[[c for c in df_all_agss if not str(c).startswith("110")]].copy()
    df[11000] = df_berlin_cases_sum
    df["11000_deaths"] = df_berlin_deaths_sum
    print(df)

    lr_has_nan = df.tail(1).isnull().values.any()
    lr_has_zero = df.tail(1).eq(0).values.any()

    # During the week easily the last row can contain NaN as of slow RKI
    # updates/Meldeverzug.
    if lr_has_nan:
        log.info("last row has NaNs")

    if lr_has_zero:
        log.info("last row has zeros")

    if lr_has_nan or lr_has_zero:
        log.info("drop last row")
        # df.head(-1) ## creates a view, I suppose
        df.drop(df.tail(1).index, inplace=True)

    # After a weekend it's possible that even more data hasn't come in yet.
    # Example:
    # 2020-03-26 01:00:00+01:00   18.0   75.0   68.0   13.0   20.0   69.0   28.0  ...     14     32     21     11    103     16  2022.0
    # 2020-03-27 01:00:00+01:00    NaN    NaN    NaN    NaN    NaN    NaN    NaN  ...     16     32     22     27    111     18     0.0
    # 2020-03-28 01:00:00+01:00    NaN    NaN    NaN    NaN    NaN    NaN    NaN  ...     20     32     27     27    121     19     0.0
    # 2020-03-29 01:00:00+01:00    NaN    NaN    NaN    NaN    NaN    NaN    NaN  ...     20     32     27     27    130     19     0.0

    lr_has_nan = df.tail(1).isnull().values.any()
    if lr_has_nan:
        log.info("(at least the) last row still has NaNs -- forward-fill")
        df.fillna(method="ffill", inplace=True)

    print(df)

    log.info("turn df to int64")
    df = df.astype("int64")
    return df


def chunks(iterable, n, fillvalue=None):
    # From itertoos recipes
    # https://stackoverflow.com/a/434411/145400
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def fetch_lks():
    """
    Conduct a synthetic query towards getting the set of Landkreise w/o being
    hard on the back-end.
    """

    # Trailing `?`.
    AG_RKI_SUMS_QUERY_BASE_URL = os.environ["AG_RKI_SUMS_QUERY_BASE_URL"]

    params = urllib.parse.urlencode(
        {
            "where": "(Meldedatum>timestamp '2020-04-09') AND (Meldedatum<timestamp '2020-04-11')",
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
    for o in objs:
        landkreise[int(o["IdLandkreis"])] = o

    log.info("Got info for %s LKs", len(landkreise))
    return landkreise


def fetch_history_for_many_ags(ags_list):
    """
    Args:
        ags_list: list of int, allgemeiner gemeindeschluessel
    """
    # Trailing `?`.
    AG_RKI_SUMS_QUERY_BASE_URL = os.environ["AG_RKI_SUMS_QUERY_BASE_URL"]
    md = "Meldedatum"
    ts = "timestamp"
    idlk = "IdLandkreis"
    t_start = "2020-03-01 22:00:00"
    d_end = datetime.today() - timedelta(days=0)
    t_end = f"{d_end.strftime('%Y-%m-%d')} 23:59:59"
    ags_padded_list = [str(ags).zfill(5) for ags in ags_list]

    # create list of quoted strings, e.g. ["'05366'", "'05370'"]
    ags_padded_list_cs = ", ".join(f"'{a}'" for a in ags_padded_list)

    where_clause = f"({md}>{ts} '{t_start}') AND ({md}<{ts} '{t_end}') AND ({idlk} IN ({ags_padded_list_cs}))"

    params = urllib.parse.urlencode(
        {
            "where": where_clause,
            "returnGeometry": "false",
            # "outFields": "SummeFall,Meldedatum,GEN",
            "outFields": "*",
            "orderByFields": "Meldedatum asc",
            "resultOffset": 0,
            "resultRecordCount": 10 ** 5,
            "f": "json",
        }
    )
    url = f"{AG_RKI_SUMS_QUERY_BASE_URL}{params}"

    log.info("Query for history for these AGSs: %s", ags_list)
    resp = requests.get(url)
    resp.raise_for_status()
    log.info("Got OK response, parse through data")
    data = resp.json()

    # This is what a feature object looks like:
    #     {
    #       "attributes": {
    #         "AnzahlFall": 1,
    #         "AnzahlTodesfall": 0,
    #         "SummeFall": 6,
    #         "SummeTodesfall": 0,
    #         "ObjectId": 72726,
    #         "Datenstand": "26.03.2020 00:00",
    #         "Meldedatum": 1584316800000,
    #         "Bundesland": "Nordrhein-Westfalen",
    #         "IdBundesland": 5,
    #         "Landkreis": "LK Euskirchen",
    #         "IdLandkreis": "05366"
    #       }
    #     }
    #
    # Flatten `attributes` away. Expect multi-ags response, i.e. aggregate by
    # ags while iterating.
    # objs = [o["attributes"] for o in data["features"]]

    data_by_ags = {}
    for ags in ags_list:
        data_by_ags[ags] = {"timestrings": [], "cases": [], "deaths": []}

    for obj in (o["attributes"] for o in data["features"]):
        # Mutate Meldedatum (milliseconds since epoch) into isoformat
        md_naive = datetime.fromtimestamp(int(obj["Meldedatum"] / 1000.0))

        # Read naive timestamp as in GER tz, and then convert value to UTC (so
        # that all tz indicators in the datetimeindex show the same offset, so
        # that we don't get mixed-tz CSV files which can be difficult to
        # parse).
        md_aware = (
            pytz.timezone("Europe/Amsterdam").localize(md_naive).astimezone(pytz.utc)
        )

        # Now this one is tricky. The timestamps we get from the RKI's ArcGIS
        # system suggest a local time of 01:00 in the morning. However, it
        # seems like this number is actually rater meaningless. The case count
        # for, say, March 27 01:00 in the morning are not (as suggested by the
        # time) for March 26, but actually appear to be end-of-day March 27
        # case counts. We don't know exactly, though. To make comparion with
        # other data sources more fair: shift this to ~6/7 pm on the same day.
        md_aware = md_aware + timedelta(hours=17)
        # obj["Meldedatum"] = md_aware.isoformat()
        ags = int(obj["IdLandkreis"])
        data_by_ags[ags]["timestrings"].append(md_aware.isoformat())
        data_by_ags[ags]["cases"].append(obj["SummeFall"])
        data_by_ags[ags]["deaths"].append(obj["SummeTodesfall"])

    # case_numbers_over_time = [o["SummeFall"] for o in objs]
    # timestrings = [o["Meldedatum"] for o in objs]
    # print(json.dumps(data_by_ags, indent=2))

    dataframes = {}
    for ags, data in data_by_ags.items():
        df = pd.DataFrame(
            data={ags: data["cases"], f"{ags}_deaths": data["deaths"]},
            index=data["timestrings"],
        )
        df.index = pd.to_datetime(df.index)
        df.index.name = "time_iso8601"
        dataframes[ags] = df

    log.info("aggregated %s dataframes", len(dataframes))
    return dataframes


if __name__ == "__main__":
    main()
