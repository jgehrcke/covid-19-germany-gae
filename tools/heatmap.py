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
import math
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

    parser.add_argument("timeseries_csv_path", metavar="7di-timeseries-csv-path")
    parser.add_argument("--label-data-source", metavar="LABEL")
    parser.add_argument("--figure-out-pprefix", metavar="PATH_PREFIX")

    args = parser.parse_args()

    matplotlib_config()

    log.info("read %s", DE_COUNTIES_GEOJSON_PATH)
    dfgeo = gpd.read_file(DE_COUNTIES_GEOJSON_PATH)

    df_7di = lib.io.parse_csv_timeseries(args.timeseries_csv_path)

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
    citycoords = [c for _, c in cities.items()]

    fig, ax = plt.subplots()

    log.info("dfgeo columns: %s", dfgeo.columns)
    print(dfgeo)
    dfgeo["centroid"] = dfgeo["geometry"].centroid

    last_c7di_vals = []
    # Each row in `dfgeo` contains information about one AGS (including the
    # polygons from the GeoJSON file). Iterate through these rows and look up
    # the last 7di value for each AGS from the `df_7di` dataframe.
    for _, row in dfgeo.iterrows():
        # Strip leading zeros from ags string.
        ags = str(int(row["AGS"]))
        last_c7di_val = df_7di[ags + "_7di"].iloc[-1]
        last_c7di_vals.append(last_c7di_val)
        # log.info("centroid: %s", row["centroid"])

    # Now add this list of 'last 7di values' as a new column to the geo df.
    dfgeo["last_c7di_val"] = last_c7di_vals

    log.info("create geo plot")
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

    log.info("plot cities")
    # Plot cities. Kudos to
    # https://juanitorduz.github.io/germany_plots/
    for c in cities:
        ax.text(
            x=cities[c][0],
            # Epsilon-shift downwards, to draw this text label below the marker.
            y=cities[c][1] - 0.09,
            s=c,
            fontsize=6,
            ha="center",
            color="#444",
        )
        ax.plot(
            cities[c][0], cities[c][1], marker="o", c="black", alpha=0.5, markersize=3
        )

    # Add special label for the county with the maximum 7di value.
    idxmax = dfgeo["last_c7di_val"].idxmax()
    print(idxmax)
    maxrow = dfgeo.iloc[idxmax]
    ax.text(
        x=maxrow["centroid"].x,
        y=maxrow["centroid"].y,
        s=str(round(maxrow["last_c7di_val"])),
        fontsize=8,
        ha="center",
        color="#eee",  # show in bright color, corresponding to dark end of color map
    )

    # Draw 7di labels for remaining counties, but not too densely.
    labels_added = []
    for _, row in dfgeo.iterrows():
        cur_row_latest_7di = round(df_7di[str(int(row["AGS"])) + "_7di"].iloc[-1])
        row["centroid"] = row["centroid"]

        # calc min distance to labels added. use pythagoras of lat/long
        # coords, approximating simple 2d surface
        if labels_added:
            # TODO: use numpy/pandas approach to speed up pairwise distance
            # calculation if performance starts to matter/suck.
            mind = min(
                math.sqrt(
                    (row["centroid"].x - c.x) ** 2 + (row["centroid"].y - c.y) ** 2
                )
                for c in labels_added
            )
            log.info("mind: %s", mind)
            if mind < 0.35:
                log.info("skip drawing this label")
                continue

        # calculate min distance to city points -- if a city point is super
        # close, then push the label 'up' a bit.
        min_distance_to_citypoints = min(
            math.sqrt((row["centroid"].x - c[0]) ** 2 + (row["centroid"].y - c[1]) ** 2)
            for c in citycoords
        )
        draw_at_x = row["centroid"].x
        draw_at_y = row["centroid"].y
        if min_distance_to_citypoints < 0.04:
            draw_at_y = draw_at_y + 0.05
        ax.text(
            x=draw_at_x,
            y=draw_at_y,
            s=str(cur_row_latest_7di),
            fontsize=7,
            ha="center",
            color="#444",
        )

        # Keep track of this label having been added.
        labels_added.append(row["centroid"])

    # In a pandas DatetimeIndex, the timezone information (if stored) is stored
    # on the column. That is, the individual timestamp when accessed with e.g.
    # df.index.values[-1] does _not_ contain tz information, it's naive. We
    # know that it's given in UTC, and with `utc=True`, pandas makes the result
    # tz-aware, explicitly annotating the datetime object with tz info for UTC.
    latest_timestamp = pd.to_datetime(df_7di.index.values[-1], utc=True)
    log.info("latest timestamp in file: %s", latest_timestamp)
    latest_timestamp_day_string = latest_timestamp.strftime("%Y-%m-%d %H:%M")
    today = NOW.strftime("%Y-%m-%d")

    # log.info("latest timestamp in data set: %s", df_7di.index.values[-1])

    # title
    ax.text(
        0.5,
        0.99,
        "7-Tage-Inzidenz",
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
        "7-day sum of newly confirmed cases per 100.000 inhabitants",
        verticalalignment="center",
        horizontalalignment="center",
        fontsize=10,
        transform=ax.transAxes,
        color="#444",
    )

    # Display current all-Germany 7di mean:
    ag7di = df_7di["germany_7di"].iloc[-1]
    ax.text(
        0.05,
        0.13,
        f"{ag7di:.1f}",
        # verticalalignment="center",
        horizontalalignment="center",
        fontsize=40,
        transform=ax.transAxes,
        color="#444",
    )
    ax.text(
        0.05,
        0.116,
        "(all Germany)",
        fontsize=8,
        transform=ax.transAxes,
        horizontalalignment="center",
        color="#444",
    )

    # footer
    ax.text(
        0.5,
        0.01,
        f"{args.label_data_source} (state: {latest_timestamp_day_string} UTC)\n",
        weight="bold",
        fontsize=8,
        horizontalalignment="center",
        transform=ax.transAxes,
        color="#666666",
    )
    ax.text(
        0.5,
        0.005,
        f"generated on {today} — " + "https://github.com/jgehrcke/covid-19-germany-gae",
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
    else:
        log.info("skip writing figure files")

    # plt.show()


def write_current_fig(pprefix):
    # Write to path prefix `pprefix` (only append file extensions).
    log.info(f"write {pprefix}.png")
    plt.savefig(f"{pprefix}.png", dpi=140)
    log.info(f"write {pprefix}.pdf")
    plt.savefig(f"{pprefix}.pdf")


def matplotlib_config():
    plt.style.use("ggplot")
    matplotlib.rcParams["figure.figsize"] = [11, 11.0]
    matplotlib.rcParams["figure.dpi"] = 100
    matplotlib.rcParams["savefig.dpi"] = 150


if __name__ == "__main__":
    matplotlib_config()
    main()
