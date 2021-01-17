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
"""

import argparse
import os
import logging
import json
import sys
from datetime import datetime

import pandas as pd
import geopandas as gpd

import seaborn
import matplotlib
import matplotlib.pyplot as plt


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import lib.tsmath
import lib.io


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


NOW = datetime.utcnow()

_tools_dir = os.path.dirname(os.path.abspath(__file__))
DE_COUNTIES_GEOJSON_PATH = os.path.join(
    _tools_dir, "..", "geodata", "DE-counties.geojson"
)
DE_AGS_POP_JSON_PATH = os.path.join(_tools_dir, "..", "ags.json")


log.info("read %s", DE_AGS_POP_JSON_PATH)
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
    parser.add_argument("--label-data-source", metavar="LABEL")
    parser.add_argument("--figure-out-pprefix", metavar="PATH_PREFIX")

    args = parser.parse_args()

    matplotlib_config()

    log.info("read %s", DE_COUNTIES_GEOJSON_PATH)
    dfgeo = gpd.read_file(DE_COUNTIES_GEOJSON_PATH)

    df_c19 = lib.io.read_csv_as_df(args.cases_timeseries_csv_path)

    df_c19_cases_norm = calc_7_day_incidence_for_each_ags(df_c19)

    cities = {
        "Berlin": (13.404954, 52.520008),
        "Köln": (6.953101, 50.935173),
        "Frankfurt": (8.682127, 50.110924),
        "Hamburg": (9.993682, 53.551086),
        "Leipzig": (12.387772, 51.343479),
        "München": (11.576124, 48.137154),
        "Dortmund": (7.468554, 51.513400),
        "Stuttgart": (9.181332, 48.777128),
        "Nürnberg": (11.077438, 49.449820),
        "Hannover": (9.73322, 52.37052),
    }

    fig, ax = plt.subplots()

    last_c7di_vals = []
    for _, row in dfgeo.iterrows():
        # Strip leading zeros from ags string in this dataframe.
        ags = str(int(row["AGS"]))
        # ags_props = AGS_PROPERTY_DICT[ags]
        # print(ags_props)
        last_c7di_val = df_c19_cases_norm[ags + "_7di"].iloc[-1]
        # row["last_c7di_val"] = last_c7di_val
        last_c7di_vals.append(last_c7di_val)

    dfgeo["last_c7di_val"] = last_c7di_vals

    dfgeo.plot(
        ax=ax,
        alpha=0.7,
        column="last_c7di_val",
        linewidth=0.1,
        edgecolor="#555",
        categorical=False,
        legend=True,
        # cmap="autumn_r",
        # This is a key decision here. Lovely background info:
        # https://seaborn.pydata.org/tutorial/color_palettes.html
        # Use a sequential one.
        cmap=seaborn.color_palette("rocket_r", as_cmap=True),
    )

    # Plot cities. Kudos to
    # https://juanitorduz.github.io/germany_plots/
    for c in cities:
        ax.text(
            x=cities[c][0],
            # Epsilon-shift upwards, to draw this text label above the marker.
            y=cities[c][1] + 0.08,
            s=c,
            fontsize=12,
            ha="center",
            color="#444",
        )
        ax.plot(cities[c][0], cities[c][1], marker="o", c="black", alpha=0.5)

    latest_timestamp = pd.to_datetime(str(df_c19_cases_norm.index.values[-1]))
    latest_timestamp_day_string = latest_timestamp.strftime("%Y-%m-%d")

    # title
    ax.text(
        0.5,
        0.99,
        '"7-Tage-Inzidenz"',
        verticalalignment="center",
        horizontalalignment="center",
        transform=ax.transAxes,
        fontsize=14,
        color="#444",
    )

    # subtitle
    ax.text(
        0.5,
        0.966,
        "(7-day sum of newly confirmed cases per 100.000 inhabitants)",
        verticalalignment="center",
        horizontalalignment="center",
        fontsize=10,
        transform=ax.transAxes,
        color="#444",
    )

    # footer
    ax.text(
        0.5,
        0.01,
        f"{latest_timestamp_day_string} — {args.label_data_source} — https://github.com/jgehrcke/covid-19-germany-gae — Dr. Jan-Philip Gehrcke",
        fontsize=8,
        horizontalalignment="center",
        transform=ax.transAxes,
        color="#666666",
    )

    # shp.plot(ax=ax, linewidth=0.5, edgecolor='0.5')
    ax.set_axis_off()
    # plt.axis('equal')

    plt.tight_layout()
    # fig_filepath_wo_ext = f"gae/static/case-rate-rw-{NOW.strftime('%Y-%m-%d')}"
    # fig_filepath_wo_ext = "plots/heatmap-7ti-rl"
    if args.figure_out_pprefix:
        write_current_fig(args.figure_out_pprefix)

    # plt.show()


def write_current_fig(pprefix):
    # Write to path prefix `pprefix` (only append file extensions).
    log.info(f"write {pprefix}.png")
    plt.savefig(f"{pprefix}.png", dpi=140)
    log.info(f"write {pprefix}.pdf")
    plt.savefig(f"{pprefix}.pdf")


def calc_7_day_incidence_for_each_ags(df):

    window_width_days = 7
    for column in df:
        # For each column in DF, add another column with the "7 Tage Inzidenz"
        # if not column.startswith("sum_"):
        ags = column

        log.info("build seven-day-rolling-window for AGS %s", ags)

        abs_change_rolling_window = lib.tsmath.build_daily_change_rate_rolling_window(
            df=df,
            column=column,
            window_width_days=window_width_days,
            sum_over_time_window=True,
        )

        latest_timestamp = pd.to_datetime(
            str(abs_change_rolling_window.index.values[-1])
        )
        latest_timestamp_day_string = latest_timestamp.strftime("%Y-%m-%d %H:%M")

        log.info("last data point time: %s", latest_timestamp_day_string)

        log.info(
            "last data point (absolute count, mean over last %s days): %s",
            window_width_days,
            int(abs_change_rolling_window.iloc[-1] / window_width_days),
        )

        if column.startswith("sum_"):
            pop = TOTAL_POPULATION_GER
        else:
            pop = AGS_PROPERTY_DICT[ags]["population"]

        log.info("normalize by population (1/100000 inhabitants), pop count: %s", pop)
        norm_change_rolling_window = abs_change_rolling_window / float(pop) * 100000.0
        log.info(
            "last data point (normalized on pop, sum over last %s days): %s",
            window_width_days,
            int(norm_change_rolling_window.iloc[-1]),
        )

        df[f"{column}_7di"] = norm_change_rolling_window
        # print(df[f"{column}_7di"])
        # sys.exit()

    print(df)
    return df


def matplotlib_config():
    plt.style.use("ggplot")
    # import seaborn as sns

    # make the gray background of gg plot a little lighter
    plt.rcParams["axes.facecolor"] = "#eeeeee"
    matplotlib.rcParams["figure.figsize"] = [11, 11.0]
    matplotlib.rcParams["figure.dpi"] = 100
    matplotlib.rcParams["savefig.dpi"] = 150
    # mpl.rcParams['font.size'] = 12


if __name__ == "__main__":
    matplotlib_config()
    main()
