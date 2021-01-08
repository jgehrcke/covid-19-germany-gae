# MIT License

# Copyright (c) 2020 - 2021 Dr. Jan-Philip Gehrcke

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
Process Gemeindeverzeichnis information published by DESTATIS at

https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html

Spreadsheet information at the time of writing:

- Original filename: AuszugGV4QAktuell.xlsx
- State of data: December 31, 2020 (according to DESTATIS)
- Downloaded on: Jan 8, 2021
- XLSX last modified: "01/07/2021, 12:33:26, Mettner, Claudia (F202)"

Structure of this sheet:

In [12]: df = pd.read_excel('AuszugGV4QAktuell.xlsx', sheet_name='Onlineprodukt_Gemeinden', header=[2,3])
In [14]: df.columns
Out[14]:
MultiIndex([(                           'Satz-art',  'Unnamed: 0_level_1'),
            (                  'Text-kenn-zeichen',  'Unnamed: 1_level_1'),
            (  'Amtlicher Regionalschlüssel (ARS)',                'Land'),
            (  'Amtlicher Regionalschlüssel (ARS)',                  'RB'),
            (  'Amtlicher Regionalschlüssel (ARS)',               'Kreis'),
            (  'Amtlicher Regionalschlüssel (ARS)',                  'VB'),
            (  'Amtlicher Regionalschlüssel (ARS)',                 'Gem'),
            (                       'Gemeindename',  'Unnamed: 7_level_1'),
            (                      'Fläche km2 1)',  'Unnamed: 8_level_1'),
            (                      'Bevölkerung2)',           'insgesamt'),
            (                      'Bevölkerung2)',            'männlich'),
            (                      'Bevölkerung2)',            'weiblich'),
            (                      'Bevölkerung2)',              'je km2'),
            (                   'Post-leit-zahl3)', 'Unnamed: 13_level_1'),
            ('Geografische Mittelpunktkoordinaten',          'Längengrad'),
            ('Geografische Mittelpunktkoordinaten',         'Breitengrad'),
            (                       'Reisegebiete', 'Unnamed: 16_level_1'),
            (                       'Reisegebiete', 'Unnamed: 17_level_1'),
            (             'Grad der Verstädterung', 'Unnamed: 18_level_1'),
            (             'Grad der Verstädterung', 'Unnamed: 19_level_1')],
           )

Goal of this module: parse this sheet, rename and process columns of interest,
drop other columns, process rows. Make this useful.

The above's data set contains only a single aggregate for Berlin.
Use a separate source for Berlin:
    https://www.statistik-berlin-brandenburg.de/
    https://www.statistik-berlin-brandenburg.de/publikationen/stat_berichte/2020/SB_A01-05-00_2020h01_BE.xlsx
    State: 30. Juni 2020
    Hard-code this into this program.

After all, enrich the /ags.json with population data for each of its AGS entries.
"""

import argparse
import os
import logging
import json
import sys

import pandas as pd


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("gv_xlsx_path", metavar="gv-xlsx-path")

    parser.add_argument("--enrich-ags-json", metavar="PATH")
    parser.add_argument("--write-ags-pop-csv", metavar="PATH")
    args = parser.parse_args()

    if args.enrich_ags_json:
        log.info("read %s", args.enrich_ags_json)
        with open(args.enrich_ags_json, "rb") as f:
            # This retains order.
            AGS_PROPERTY_MAP = json.loads(f.read().decode("utf-8"))

    df = read_xlsx_rename_drop(args.gv_xlsx_path)
    df_calculate_and_add_ags_column(df)
    df = generate_df_pop_by_ags(df)

    log.info("dataframe for AGS <-> population association:\n\n%s", df)

    if args.write_ags_pop_csv:
        log.info("write AGS <-> population CSV file to %s", args.write_ags_pop_csv)
        df.to_csv(args.write_ags_pop_csv)

    if args.enrich_ags_json:
        log.info("add population data to %s", args.enrich_ags_json)
        for ags, row in df.iterrows():
            assert str(ags) in AGS_PROPERTY_MAP
            AGS_PROPERTY_MAP[str(ags)]["population"] = int(row["population"])

        log.info("add berlin districts to AGS_PROPERTY_MAP")
        add_resolution_to_berlin(AGS_PROPERTY_MAP)

        # Skip those entries that do not have the populuation key set (expected
        # for AGS 3152 "LK Göttingen (alt)". Minus the total for Berlin, because
        # there's a double count.
        checksum = (
            sum(
                v["population"]
                for k, v in AGS_PROPERTY_MAP.items()
                if "population" in v
            )
            - AGS_PROPERTY_MAP["11000"]["population"]
        )

        log.info(
            "total GER population checksum for to-be-written %s: %s",
            args.enrich_ags_json,
            checksum,
        )

        log.info("rewrite %s", args.enrich_ags_json)
        with open(args.enrich_ags_json, "wb") as f:
            # Note that JSON only allows text keys, not numbers.
            f.write(
                json.dumps(AGS_PROPERTY_MAP, indent=2, ensure_ascii=False).encode(
                    "utf-8"
                )
            )


def add_resolution_to_berlin(ags_property_map):
    """
    Data from https://www.statistik-berlin-brandenburg.de/
    SB_A01-05-00_2020h01_BE.xlsx
    June 2020
    """
    # AGS 11000 represents all of Berlin, i.e. includes 110XX. The total of
    # 3669491 is the sum of the individual SK numbers below, as provided by
    # statistik-berlin-brandenburg.de. Note that the Berlin total provided by
    # DESTATIS in the data set used for non-Berlin AGS is 3762456, i.e. it
    # deviates by about ~100k. The DESTATIS data set seems to be slightly newer
    # (by half a year: summer 2020 vs end of 2020), but I think it's better to
    # have Berlin-internal consistency here.
    ags_property_map["11000"]["population"] = 3669491

    # SK Berlin Mitte
    ags_property_map["11001"]["population"] = 380917

    # SK Berlin Friedrichshain-Kreuzberg
    ags_property_map["11002"]["population"] = 290083

    # SK Berlin Pankow
    ags_property_map["11003"]["population"] = 409454

    # SK Berlin Charlottenburg-Wilmersdorf
    ags_property_map["11004"]["population"] = 342950

    # SK Berlin Spandau
    ags_property_map["11005"]["population"] = 244458

    # SK Berlin Steglitz-Zehlendorf
    ags_property_map["11006"]["population"] = 308582

    # SK Berlin Tempelhof-Schöneberg
    ags_property_map["11007"]["population"] = 351062

    # SK Berlin Neukölln
    ags_property_map["11008"]["population"] = 328666

    # SK Berlin Treptow-Köpenick
    ags_property_map["11009"]["population"] = 273817

    # SK Berlin Marzahn-Hellersdorf
    ags_property_map["11010"]["population"] = 271311

    # SK Berlin Lichtenberg
    ags_property_map["11011"]["population"] = 294937

    # SK Berlin Reinickendorf
    ags_property_map["11012"]["population"] = 266219


def generate_df_pop_by_ags(df):

    log.info("aggregate (sum) population by AGS")
    df_pop = df.drop(columns=list(set(df.columns) - set(["ags", "population_total"])))
    df_pop = df_pop.rename(columns={"population_total": "population"})

    df_pop_by_ags = df_pop.groupby("ags").sum()
    df_pop_by_ags.index = df_pop_by_ags.index.astype(int)
    df_pop_by_ags.sort_index(inplace=True)

    # Not contained in this dataset:
    #
    # "3152": {
    #     "name": "LK Göttingen (alt)",
    #     "state": "Niedersachsen",
    #     "lat": 51.5369,
    #     "lon": 9.8568
    # },
    #
    # 110XX -- Berlin districts which are not actually LKs.

    # Now, there may still be a small number of AGSs that are virtual,
    # indicated by population count of 0 (also set in the original spreadsheet)

    dropthis = df_pop_by_ags[df_pop_by_ags.population == 0]
    log.info("delete these rows: %s", dropthis)
    df_pop_by_ags = df_pop_by_ags[df_pop_by_ags.population != 0]

    log.info("total population checksum: %s", df_pop_by_ags["population"].sum())

    return df_pop_by_ags


def df_calculate_and_add_ags_column(df):
    # Build Amtlicher Gemeindeschluessel (AGS, string)
    # Turn floaty values into integer, and then into string.
    # Kreis needs to be zero-padded to width 2: 1 -> 01.
    df["ags"] = (
        df["land_id"].astype(int).astype(str)
        + df["regbez_id"].astype(int).astype(str)
        + df["kreis_id"].astype(int).astype(str).str.zfill(2)
    )


def read_xlsx_rename_drop(xlsx_path):
    # Parsing this seems to require pandas 1.2.0 and openpyxl, xlrd.
    # do: `pip install xlrd openpyxl pandas --upgrade`
    # Only read fourth row (idx 3) as column headings.
    log.info("parse %s", xlsx_path)
    df = pd.read_excel(xlsx_path, sheet_name="Onlineprodukt_Gemeinden", header=[3])
    log.info("parsed columns: %s", df.columns)

    rename_dict = {
        "Land": "land_id",
        "RB": "regbez_id",
        "Kreis": "kreis_id",
        "VB": "gem_verb_id",
        "Gem": "gem_id",
        "Unnamed: 7": "gem_name",
        "insgesamt": "population_total",
        "Längengrad": "geo_longitude",
        "Breitengrad": "geo_latitude",
    }

    df = df.rename(columns=rename_dict)
    log.info("columns after rename: %s", df.columns)

    keep_cols = [v for k, v in rename_dict.items()]

    log.info("drop all columns except for %s", keep_cols)
    df = df.drop(columns=list(set(df.columns) - set(keep_cols)))
    log.info("columns after drop: %s", df.columns)

    log.info(
        "drop all rows that do not have population or regbez set -- these are mid-sheet headings"
    )

    log.info("rowcount before: %s", len(df))
    df = df.dropna(subset=["population_total", "regbez_id"])
    log.info("rowcount after: %s", len(df))

    return df


if __name__ == "__main__":
    main()
