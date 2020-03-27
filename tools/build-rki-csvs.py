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

    # csv_filepath = "data-rki-by-lk.csv"
    # log.info("write data to CSV file %s", csv_filepath)
    # with open(csv_filepath, "wb") as f:
    #     f.write(df.to_csv().encode("utf-8"))

    # sys.exit()

    log.info("Turn DatetimeIndex into index of ISO 8601 strings")

    # CPython 3.7 for the %z format specifier behavior.
    df_by_bl.index = df_by_bl.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_bl.index.name = "time_iso8601"
    print(df_by_bl)

    df_by_lk.index = df_by_lk.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_by_lk.index.name = "time_iso8601"
    print(df_by_lk)

    csv_filepath_bk = "cases-rki-by-state.csv"
    log.info("write data to CSV file %s", csv_filepath_bk)
    with open(csv_filepath_bk, "wb") as f:
        f.write(df_by_bl.to_csv().encode("utf-8"))

    csv_filepath_lk = "cases-rki-by-ags.csv"
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
    log.info("fetch LK-resolved RKI data from arcgis system")

    # `landkreise` is a dictionary where each item represents a Landkreis or
    # kreisfreie Stadt. Keys are AGS, value has some detail about Landkreis
    # such as Bundesland and LK name.
    landkreise = fetch_lks()

    ags_list_ref = [int(a) for a in AGS_BL_MAP.keys()]
    ags_list_from_rki = [int(a) for a in landkreise.keys()]

    dataframes = []
    for subset in chunks(ags_list_from_rki, 100):
        # The chunker fills the last chunk with Nones.
        agss = [ags for ags in subset if ags is not None]

        # `ndfs` is a dict with AGS as key, and a per-LK dataframe as val.
        ndfs = fetch_history_for_many_ags(agss)

        # I have seen that this can happen. Not quite sure why/now.
        for ags, df in ndfs.items():
            if not len(df):
                log.warning("dataframe empty for ags %s", ags)

        log.info("concatenate non-empty chunk dataframes")
        dfs_chunk = [df[ags] for ags, df in ndfs.items() if len(df)]

        if not dfs_chunk:
            log.warning("no non-empty chunk dataframes, skip chunk")
            continue

        log.info("build chunk df from %s non-empty ags series", len(dfs_chunk))
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
    # The RKI data set hasthe  11001..11012 for Berlin.
    assert len(added_wrt_ref) == 12
    for a in added_wrt_ref:
        assert str(a).startswith("110")

    # Give Berlin some special treatment. Aggregate.
    # Create view from big DF with Berlin AGSs.
    df_berlin_ags = df_all_agss[[c for c in df_all_agss if str(c).startswith("110")]]
    print(df_berlin_ags)
    df_berlin_sum = df_berlin_ags.sum(axis=1)
    print(df_berlin_sum)

    # "Final" dataframe, with one column for all of Berlin.
    df = df_all_agss[[c for c in df_all_agss if not str(c).startswith("110")]].copy()
    df[11000] = df_berlin_sum
    print(df)

    # df.index = df.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    # df.index.name = "time_iso8601"
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
            "where": "(Meldedatum>timestamp '2020-03-17') AND (Meldedatum<timestamp '2020-03-21')",
            "returnGeometry": "false",
            "outFields": "IdLandkreis, Landkreis, Bundesland",
            "orderByFields": "IdLandkreis asc",
            "resultOffset": 0,
            "resultRecordCount": 100000,
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
    d_end = datetime.today() - timedelta(days=1)
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
            "resultRecordCount": 2000,
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
        md_aware = pytz.timezone("Europe/Amsterdam").localize(md_naive)
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
        df = pd.DataFrame(data={ags: data["cases"]}, index=data["timestrings"])
        df.index = pd.to_datetime(df.index)
        df.index.name = "time_iso8601"
        dataframes[ags] = df

    log.info("aggregated %s dataframes", len(dataframes))
    return dataframes


if __name__ == "__main__":
    main()
