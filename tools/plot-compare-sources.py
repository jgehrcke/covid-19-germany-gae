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
import logging
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import bokeh.plotting
import bokeh.models
from bokeh.layouts import column, layout
import bokeh.io
import bokeh.embed
import bokeh.resources

import jinja2

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


NOW = datetime.utcnow()


def main():

    # About "Meldedatum", vom RKI dashboard: Für die Darstellung der
    # neuübermittelten Fälle pro Tag wird das Meldedatum verwendet – das Datum,
    # an dem das lokale Gesundheitsamt Kenntnis über den Fall erlangt und ihn
    # elektronisch erfasst hat.

    # Zwischen der Meldung durch die Ärzte und Labore an das Gesundheitsamt und
    # der Übermittlung der Fälle an die zuständigen Landesbehörden und das RKI
    # können einige Tage vergehen (Melde- und Übermittlungsverzug). Jeden Tag
    # werden dem RKI neue Fälle übermittelt, die am gleichen Tag oder bereits
    # an früheren Tagen an das Gesundheitsamt gemeldet worden sind. Diese Fälle
    # werden in der Grafik Neue COVID-19-Fälle/Tag dann bei dem jeweiligen
    # Datum ergänzt.

    START_DATE = "2020-03-09"

    def _build_case_rate(df):
        # Get time differences (unit: seconds) in the df's datetimeindex. `dt`
        # is a magic accessor that yields an array of time deltas.
        dt_seconds = pd.Series(df.index).diff().dt.total_seconds()
        # Construct new series with original datetimeindex as index and time
        # differences (unit: days) as values.
        dt_days = pd.Series(dt_seconds) / 86400.0
        dt_days.index = df.index
        # print(dt_days)
        cases_change_per_day = df["sum_cases"].diff().div(dt_days)
        df["cases_change_per_day"] = cases_change_per_day
        print(df)

        # increase resolution and forward-fill values. Could also use
        # `interpolate()` but that's too artificial, I think it's fair to see
        # the actual discrete jumps in data as of "batch processing".
        df_case_change = df["cases_change_per_day"].resample("1H").pad()

        print(type(df_case_change))
        # sys.exit()

        # Should be >= 7 to be meaningful.
        window_width_days = 5
        window = df_case_change.rolling(window="%sD" % window_width_days)

        # Manually build rolling window mean.
        wdw_norm = window.sum() / (window_width_days * 24.0)

        # During the rolling window analysis the value derived from the current
        # window position is assigned to the right window boundary (i.e. to the
        # newest timestamp in the window). For presentation it is more convenient
        # and intuitive to have it assigned to the temporal center of the time
        # window. Invoking `rolling(..., center=True)` however yields
        # `NotImplementedError: center is not implemented for datetimelike and
        # offset based windows`. As a workaround, shift the data by half the window
        # size to 'the left': shift the timestamp index by a constant / offset.
        offset = pd.DateOffset(days=window_width_days / 2.0)
        wdw_norm.index = wdw_norm.index - offset
        print(wdw_norm)
        # sys.exit()

        # cut the last 2 days worth of data, at least for RKI this is just too
        # much affected by Meldeverzug
        d_end = NOW - timedelta(days=3)
        # t_end = f"{d_end.strftime('%Y-%m-%d')} 23:59:59"
        return wdw_norm[:f"{d_end.strftime('%Y-%m-%d')}"]

    df_mixed_data = pd.read_csv(
        "data.csv",
        index_col=["time_iso8601"],
        parse_dates=["time_iso8601"],
        date_parser=lambda col: pd.to_datetime(col, utc=True),
    )[START_DATE:]
    df_mixed_data.index.name = "time"
    df_mixed_case_rate_rw = _build_case_rate(df_mixed_data)[START_DATE:]

    df_rl = pd.read_csv(
        "cases-rl-crowdsource-by-state.csv",
        index_col=["time_iso8601"],
        parse_dates=["time_iso8601"],
    )[START_DATE:]
    df_rl.index.name = "time"
    df_rl_case_rate_rw = _build_case_rate(df_rl)[START_DATE:]

    df_rki = pd.read_csv(
        "cases-rki-by-state.csv",
        index_col=["time_iso8601"],
        parse_dates=["time_iso8601"],
    )[START_DATE:]
    df_rki.index.name = "time"
    df_rki_case_rate_rw = _build_case_rate(df_rki)[START_DATE:]

    df_jhu = jhu_csse_csv_to_dataframe(os.environ["JHU_TS_CSV_PATH"], "germany")[
        START_DATE:
    ]
    df_jhu.index.name = "time"
    df_jhu_case_rate_rw = _build_case_rate(df_jhu)[START_DATE:]

    # Normalize for 'sum_cases' plots
    for _df in [df_rki, df_jhu, df_mixed_data, df_rl]:
        _df["sum_cases"] = _df["sum_cases"] / 10000

    plt.figure()

    ax = df_rki["sum_cases"].plot(linestyle="solid", marker="x", color="red",)
    df_rl["sum_cases"].plot(linestyle="solid", marker="x", color="black", ax=ax)
    df_mixed_data["sum_cases"].plot(
        linestyle="dashdot", marker="x", color="black", ax=ax
    )
    df_jhu["sum_cases"].plot(linestyle="dashdot", marker="x", color="gray", ax=ax)

    ax.legend(
        [
            "RKI data, by Meldedatum",
            "Risklayer/Tagesspiegel crowdsource data, daily snapshots",
            "ZEIT ONLINE, daily snapshots",
            "JHU (GitHub CSSEGISandData/COVID-19)",
        ],
        numpoints=4,
        handlelength=8,
    )

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))

    plt.xlabel("Time")
    plt.ylabel("cumulative case count, all Germany / 10^4")
    # plt.title("COVID-19 case count, Germany, comparison of data sources")
    # set_title('Override command rate (from both DC/OS repositories)')
    # set_subtitle('Arithmetic mean over rolling time window')
    # plt.tight_layout(rect=(0, 0, 1, 0.95))

    plt.tight_layout()
    fig_filepath_wo_ext = (
        f"gae/static/data-sources-comparison-{NOW.strftime('%Y-%m-%d')}"
    )
    plt.savefig(fig_filepath_wo_ext + ".png", dpi=150)
    plt.savefig(fig_filepath_wo_ext + ".pdf")

    # -----------

    plt.figure()

    ax = df_rki["cases_change_per_day"].plot(linestyle="None", marker="x", color="red",)
    df_rki_case_rate_rw.plot(linestyle="solid", marker=None, color="blue", ax=ax)
    df_rl_case_rate_rw.plot(linestyle="solid", marker=None, color="black", ax=ax)
    df_jhu_case_rate_rw.plot(linestyle="solid", marker=None, color="green", ax=ax)
    # df_rl["cases_change_per_day"].plot(
    #     linestyle="solid", marker="x", color="black", ax=ax
    # )
    # df_mixed_data["cases_change_per_day"].plot(
    #     linestyle="dashdot", marker="x", color="black", ax=ax
    # )
    # df_jhu["cases_change_per_day"].plot(
    #     linestyle="dashdot", marker="x", color="gray", ax=ax
    # )

    ax.legend(
        [
            "RKI data, by Meldedatum",
            "RKI rwdw",
            "RL rwdw",
            "JHU rwdw"
            # "Risklayer/Tagesspiegel crowdsource data, daily snapshots",
            # "ZEIT ONLINE, daily snapshots",
            # "JHU (GitHub CSSEGISandData/COVID-19)",
        ],
        numpoints=4,
        handlelength=8,
    )

    # ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))

    plt.xlabel("")
    plt.ylabel("COVID-19 cumulative case count, change per day (all Germany)")
    # plt.yscale("log")
    # ax.set_ylim(bottom=600)
    # ax.set_yticks([500, 1000, 1500, 2000, 2500, 3000, 3500, 5000, 7000, 9000])
    import matplotlib.ticker as ticker

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: "{:g}".format(y)))
    # plt.title("COVID-19 case count, Germany, comparison of data sources")
    # set_title('Override command rate (from both DC/OS repositories)')
    # set_subtitle('Arithmetic mean over rolling time window')
    # plt.tight_layout(rect=(0, 0, 1, 0.95))

    plt.tight_layout()
    # fig_filepath_wo_ext = (
    #     f"gae/static/data-sources-comparison-{NOW.strftime('%Y-%m-%d')}"
    # )
    # plt.savefig(fig_filepath_wo_ext + ".png", dpi=150)
    # plt.savefig(fig_filepath_wo_ext + ".pdf")

    # title=f"Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}",

    plt.show()

    # plot_with_bokeh(df_rki, df_jhu, df_mixed_data, df_rl)


def _set_common_bokeh_fig_props(fig):
    fig.toolbar.active_drag = None
    fig.toolbar.active_scroll = None
    fig.toolbar.active_tap = None
    fig.outline_line_color = "#333333"
    fig.outline_line_width = 1
    fig.outline_line_alpha = 0.7

    fig.title.text_font_size = "10px"

    fig.legend.label_text_font_size = "10px"
    # fig.legend.label_text_font = "'Open Sans Condensed', sans-serif"
    fig.legend.spacing = 0
    fig.legend.margin = 3
    fig.legend.label_standoff = 5
    fig.legend.label_height = 0

    # import json
    # print(json.dumps(dir(fig.legend), indent=2))

    # fig.text_font_size = "12pt"
    fig.xaxis.ticker.desired_num_ticks = 21

    fig.xaxis.formatter = bokeh.models.DatetimeTickFormatter(days=["%b-%d"])
    fig.xaxis.major_label_orientation = 3.1415 / 4 + 0.5

    # fig.xaxis.axis_label = "Date"
    fig.xaxis.axis_label_text_font_size = "16px"
    fig.xaxis.major_label_text_font_size = "10px"
    fig.xaxis.axis_label_text_font_style = "normal"

    fig.y_range.start = 0
    # fig.yaxis.axis_label = "confirmed cases / 10000"
    fig.yaxis.axis_label_text_font_size = "10px"
    fig.yaxis.axis_label_text_font_style = "normal"
    fig.yaxis.major_label_text_font_size = "10px"


def plot_with_bokeh(df_rki, df_jhu, df_mixed_data, df_rl):

    # html_file_path = 'bokeh-comp-plot.html'
    # bokeh.plotting.output_file(html_file_path)
    # bokeh.io.curdoc().theme = "dark_minimal"

    cname = "sum_cases"

    fig = bokeh.plotting.figure(
        # title=f"Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}",
        title="Germany, cumulative cases / 10000",
        x_axis_type="datetime",
        toolbar_location=None,
        background_fill_color="#eeeeee",
        height=450,
    )

    # Scatter and line seemingly need to be done separately.
    # RKI
    fig.line(
        "time",
        cname,
        line_color="red",
        line_width=2,
        line_dash="solid",
        legend_label="RKI data, by Meldedatum",
        source=bokeh.models.ColumnDataSource(data=df_rki),
    )
    fig.scatter(
        "time",
        cname,
        marker="x",
        line_color="red",
        line_width=2,
        size=8,
        source=bokeh.models.ColumnDataSource(data=df_rki),
    )

    # JHU
    fig.line(
        "time",
        "sum_cases",
        line_color="black",
        line_width=1,
        line_dash="solid",
        legend_label="JHU (GitHub)",
        source=bokeh.models.ColumnDataSource(data=df_jhu),
    )
    fig.scatter(
        "time",
        "sum_cases",
        marker="x",
        line_color="black",
        line_width=1,
        size=8,
        source=bokeh.models.ColumnDataSource(data=df_jhu),
    )

    # Risklayer
    fig.line(
        "time",
        "sum_cases",
        line_color="gray",
        line_width=1,
        line_dash="dashdot",
        legend_label="Risklayer / Tagesspiegel",
        source=bokeh.models.ColumnDataSource(data=df_rl),
    )
    fig.scatter(
        "time",
        "sum_cases",
        marker="x",
        line_color="gray",
        line_width=1,
        size=8,
        source=bokeh.models.ColumnDataSource(data=df_rl),
    )

    fig.line(
        "time",
        "sum_cases",
        line_color="gray",
        line_width=1,
        line_dash="solid",
        legend_label="ZEIT ONLINE",
        source=bokeh.models.ColumnDataSource(data=df_mixed_data),
    )
    fig.scatter(
        "time",
        "sum_cases",
        marker="x",
        line_color="gray",
        line_width=1,
        size=8,
        source=bokeh.models.ColumnDataSource(data=df_mixed_data),
    )

    # fig.line(
    #     "time",
    #     "sum_cases",
    #     marker="x",
    #     size=8,
    #     line_color="black",
    #     line_width=3,
    #     ,
    #     source=bokeh.models.ColumnDataSource(data=df_jhu),
    # )

    _set_common_bokeh_fig_props(fig)

    fig.legend.location = "top_left"

    templ_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
    template = templ_env.get_template("gae/static/index.html.template")

    html = bokeh.embed.file_html(
        column(fig, figdiff, sizing_mode="stretch_both"),
        template=template,
        resources=bokeh.resources.CDN,
        template_variables={"today_string": NOW.strftime("%Y-%m-%d")},
    )

    with open("gae/static/index.html", "wb") as f:
        f.write(html.encode("utf-8"))


def jhu_csse_csv_to_dataframe(data_file_path, location_name):
    """
    data_file_path: expect an instance of `time_series_19-covid-Confirmed.csv`
    from https://github.com/CSSEGISandData/COVID-19/

    location_name: the lower-cased version of this must be a column in the
    processed data set.
    """
    log.info("parse JHU data file")
    df = pd.read_csv(data_file_path)

    log.info("process JHU data file")
    # Merge location names into somewhat more managable identifiers.
    countries = [
        "_".join(c.lower().split()) if c != "nan" else ""
        for c in list(df["Country/Region"].astype("str"))
    ]
    provinces = [
        "_".join(p.lower().split()) if p != "nan" else ""
        for p in list(df["Province/State"].astype("str"))
    ]

    countries = [c.replace(",", "").replace(".", "") for c in countries]
    provinces = [p.replace(",", "").replace(".", "") for p in provinces]

    df["where"] = [f"{c}_{p}" if p else c for c, p in zip(countries, provinces)]

    # Make each column represent a location, and each row represent a day
    # (date).

    df.drop(["Lat", "Long", "Country/Region", "Province/State"], axis=1, inplace=True)

    df = df.set_index("where")
    df = df.transpose()

    # Parse date strings into pandas DateTime objects, set proper
    # DateTimeIndex.
    normalized_date_strings = [
        "/".join(t.zfill(2) for t in o.split("/")) for o in list(df.index)
    ]
    df.index = normalized_date_strings
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")

    df.index.name = "date"
    # df.sort_index(inplace=True)

    # Only return series for specific location

    loc = location_name.lower()
    # rename column for consistency with other dfs
    df["sum_cases"] = df[loc]
    return df["sum_cases"].to_frame()


def matplotlib_config():
    plt.style.use("ggplot")
    matplotlib.rcParams["figure.figsize"] = [10.5, 7.0]
    matplotlib.rcParams["figure.dpi"] = 100
    matplotlib.rcParams["savefig.dpi"] = 150
    # mpl.rcParams['font.size'] = 12


if __name__ == "__main__":
    matplotlib_config()
    main()
