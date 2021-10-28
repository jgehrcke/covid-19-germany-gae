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
import functools
import logging
import json
import multiprocessing
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
    parser.add_argument("timeseries_csv_path", metavar="7di-timeseries-csv-path")
    parser.add_argument("--label-data-source", metavar="LABEL")
    parser.add_argument("--figure-out-pprefix", metavar="PATH_PREFIX")
    args = parser.parse_args()

    matplotlib_config()

    log.info("read %s", DE_COUNTIES_GEOJSON_PATH)
    dfgeo = gpd.read_file(DE_COUNTIES_GEOJSON_PATH)
    df_7di = lib.io.parse_csv_timeseries(args.timeseries_csv_path)

    # print(df_7di)

    largest_7di_value = df_7di.max().max()
    log.info("largest 7di value: %s", largest_7di_value)

    log.info("dfgeo columns: %s", dfgeo.columns)
    # print(dfgeo)

    dfgeo["centroid"] = dfgeo["geometry"].centroid
    datapoint_count = len(df_7di)
    row_indices = list(range(datapoint_count))
    log.info("row indices: %s", row_indices)

    # Create one image file per row
    # for rowindex in row_indices:
    #     create_figure_for_row_index(args, dfgeo, df_7di, largest_7di_value, rowindex)

    # Do the same, but distribute work across N processes
    create_figure_func = functools.partial(
        create_figure_for_row_index, args, dfgeo, df_7di, largest_7di_value
    )
    with multiprocessing.Pool(12) as pool:
        # pool.map(create_figure_func, row_indices[:5])
        pool.map(create_figure_func, row_indices)


def create_figure_for_row_index(args, dfgeo, df_7di, largest_7di_value, rowindex):
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
    # citycoords = [c for _, c in cities.items()]

    fig, ax = plt.subplots()

    # 7DI values for all AGSs for the specific 'row' (i.e. point in time)
    c7di_vals = []

    # Each row in `dfgeo` contains information about one AGS (including the
    # polygons from the GeoJSON file). Iterate through these rows and look up
    # the last 7di value for each AGS from the `df_7di` dataframe.
    for _, row in dfgeo.iterrows():
        # Strip leading zeros from ags string.
        ags = str(int(row["AGS"]))
        if ags == "16056":
            # Fall back to using the 7DI data from 16063, see
            # https://github.com/jgehrcke/covid-19-germany-gae/issues/1748
            # 16056 and 16063 are now reported together under 16063.
            log.debug(
                "for Eisenach AGS 16056 use 7DI data from Wartburgkreis AGS 16063"
            )
            ags = "16063"
        c7di_val = df_7di[ags + "_7di"].iloc[rowindex]
        c7di_vals.append(c7di_val)
        # log.info("centroid: %s", row["centroid"])

    # Now add this list of 'last 7di values' as a new column to the geo df.
    dfgeo["c7di_val"] = c7di_vals

    log.debug("create geo plot")
    dfgeo.plot(
        ax=ax,
        alpha=0.7,
        column="c7di_val",
        linewidth=0.1,
        edgecolor="#555",
        categorical=False,
        legend=True,
        vmin=0,
        vmax=largest_7di_value,
        # cmap="autumn_r",
        # This is a key decision here. Lovely background info:
        # https://seaborn.pydata.org/tutorial/color_palettes.html
        # Use a sequential one.
        # cmap=seaborn.color_palette("rocket_r", as_cmap=True),
        cmap=seaborn.color_palette("icefire", as_cmap=True),
    )

    # Plot cities. Kudos to
    # https://juanitorduz.github.io/germany_plots/
    for c in cities:
        ax.text(
            x=cities[c][0],
            # Epsilon-shift downwards, to draw this text label below the marker.
            y=cities[c][1] - 0.09,
            s=c,
            fontsize=8,
            ha="center",
            color="#444",
        )
        ax.plot(
            cities[c][0], cities[c][1], marker="o", c="black", alpha=0.5, markersize=3
        )

    # Add special label for the county with the maximum 7di value.
    idxmax = dfgeo["c7di_val"].idxmax()
    valmax = dfgeo["c7di_val"].max()

    if valmax < 350:
        col = "#222"  # dark color
    elif valmax < 600:
        col = "#eee"  # bright-ish color
    else:
        col = "#000"
    # print(idxmax)
    maxrow = dfgeo.iloc[idxmax]
    ax.text(
        x=maxrow["centroid"].x,
        y=maxrow["centroid"].y,
        s=str(round(maxrow["c7di_val"])),
        fontsize=8,
        weight="bold",
        ha="center",
        va="center",
        color=col,
    )

    # In a pandas DatetimeIndex, the timezone information (if stored) is stored
    # on the column. That is, the individual timestamp when accessed with e.g.
    # df.index.values[-1] does _not_ contain tz information, it's naive. We
    # know that it's given in UTC, and with `utc=True`, pandas makes the result
    # tz-aware, explicitly annotating the datetime object with tz info for UTC.
    timestamp = pd.to_datetime(df_7di.index.values[rowindex], utc=True)
    log.info("timestamp corresponding to rowindex %s: %s", rowindex, timestamp)
    timestamp_day_string = timestamp.strftime("%Y-%m-%d %H:%M")
    timestamp_monthyear_string = timestamp.strftime("%B %d,\n%Y ")
    today = NOW.strftime("%Y-%m-%d")

    # log.info("latest timestamp in data set: %s", df_7di.index.values[-1])
    # title
    ax.text(
        0.5,
        0.99,
        "Germany: COVID-19 7-day incidence over time",
        verticalalignment="center",
        horizontalalignment="center",
        transform=ax.transAxes,
        fontsize=14,
        color="#444",
    )

    # subtitle
    ax.text(
        0.5,
        0.969,
        "7-day sum of newly confirmed cases per 100.000 inhabitants",
        verticalalignment="center",
        horizontalalignment="center",
        fontsize=9,
        transform=ax.transAxes,
        color="#444",
    )

    # Display current all-Germany 7di mean:
    ag7di = df_7di["germany_7di"].iloc[rowindex]
    ax.text(
        0.00,
        0.03,
        f"{ag7di:.1f}",
        # verticalalignment="center",
        horizontalalignment="left",
        fontsize=24,
        transform=ax.transAxes,
        color="#444",
    )
    ax.text(
        0.00,
        0.015,
        "(all Germany)",
        fontsize=8,
        transform=ax.transAxes,
        horizontalalignment="left",
        color="#444",
    )

    ax.text(
        0.00,
        0.13,
        f"{timestamp_monthyear_string}",
        # verticalalignment="center",
        horizontalalignment="left",
        fontsize=16,
        transform=ax.transAxes,
        color="#444",
    )

    # footer
    ax.text(
        1,
        0.01,
        f"{args.label_data_source} (state: {timestamp_day_string} UTC)\n",
        # weight="bold",
        fontsize=7,
        horizontalalignment="right",
        transform=ax.transAxes,
        color="#666666",
    )
    ax.text(
        1,
        0.005,
        f"generated on {today} — " + "https://github.com/jgehrcke/covid-19-germany-gae",
        fontsize=7,
        horizontalalignment="right",
        transform=ax.transAxes,
        color="#666666",
    )

    # shp.plot(ax=ax, linewidth=0.5, edgecolor='0.5')
    ax.set_axis_off()
    # plt.axis('equal')

    # location for the zoomed portion
    miniplot = plt.axes([0.00, 0.015, 0.5, 0.078])
    # sub_axes.plot(df_7di["germany_7di"], Y_detail)
    df_7di["germany_7di"].plot(xticks=[], xlabel="", ylabel="", yticks=[])
    miniplot.plot(
        [df_7di.index.values[rowindex]],
        [df_7di["germany_7di"].iloc[rowindex]],
        marker="o",
        markersize=5,
        color="red",
    )
    # transparent background (face)
    miniplot.set_facecolor((0.0, 0.0, 1.0, 0.0))  #'#fff')

    # Do not draw (white) frame around axes
    miniplot.set_frame_on(False)

    plt.tight_layout()
    # fig_filepath_wo_ext = f"gae/static/case-rate-rw-{NOW.strftime('%Y-%m-%d')}"
    # fig_filepath_wo_ext = "plots/heatmap-7ti-rl"
    if args.figure_out_pprefix:
        write_current_fig(args.figure_out_pprefix + "_" + str(rowindex).zfill(5))
    else:
        log.info("skip writing figure files")


def write_current_fig(pprefix):
    # Write to path prefix `pprefix` (only append file extensions).
    log.info(f"write {pprefix}.png")
    plt.savefig(f"{pprefix}.png", dpi=140)


def matplotlib_config():
    plt.style.use("ggplot")
    matplotlib.rcParams["figure.figsize"] = [11, 11.0]
    matplotlib.rcParams["figure.dpi"] = 100
    matplotlib.rcParams["savefig.dpi"] = 150


if __name__ == "__main__":
    matplotlib_config()
    main()
