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

import io
import logging
import sys
import re
import sys
import time
from textwrap import dedent
from datetime import datetime


import numpy as np
import pandas as pd
import scipy.optimize
import requests
import pytz

# from bokeh.plotting import figure, output_file, show
import bokeh.plotting
import bokeh.models
from bokeh.layouts import column, layout

# from bokeh.models import ColumnDataSource, Div


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)

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

STATE_ISONAME_NAME_MAP = {v: k for k, v in STATE_NAME_ISONAME_MAP.items()}


def main():

    # Parse iso 8601 timestrings into native DatetimeIndex.
    df = pd.read_csv(
        sys.argv[1],
        index_col=["time_iso8601"],
        parse_dates=["time_iso8601"],
        date_parser=lambda col: pd.to_datetime(col, utc=True),
    )["2020-03-10":]

    # Don't show the last two days for RKI data, they are too affected by
    # Meldeverzug.
    df = df.head(-2)
    df.index.name = "date"

    for state_isoname in STATE_ISONAME_NAME_MAP:
        generate_plot_html_file(
            df,
            cname=state_isoname,  # + "_cases",
            fullname=STATE_ISONAME_NAME_MAP[state_isoname],
            shortname=state_isoname,
        )

    generate_plot_html_file(
        df, cname="sum_cases", fullname="all states/counties", shortname="DEU",
    )


def generate_plot_html_file(df_case_data, cname, fullname, shortname):
    log.info("generate plot for %s", shortname)
    now = datetime.utcnow()
    html_file_path = f"plot-{shortname}.html"

    fit_start = "2020-03-10"
    fit_end = "2020-03-21"
    cases_total_fit, doubling_time_days = expfit(
        df_case_data, cname, fit_start, fit_end
    )

    preamble_text = dedent(
        f"""
    <h2>Confirmed COVID-19 cases for Germany, {fullname}, over time</h2>

    Background information and code: <a href="https://github.com/jgehrcke/covid-19-germany-gae">github.com/jgehrcke/covid-19-germany-gae</a>

    Data sources: Gesundheitsministerien (aggregated by RKI, ZEIT ONLINE)

    Author: <a href="https://gehrcke.de">Dr. Jan-Philip Gehrcke</a>

    Data points from before March 10, 2020 are ignored.

    Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}

    Last case count: {df_case_data[cname][-1]} ({df_case_data.index[-1].strftime("%Y-%m-%d")})

    Exponential fit between {fit_start} and {fit_end} (doubling time was: ~{doubling_time_days:.1f} days).

    This mildly suggests that the numbers do not grow exponentially (anymore?).
    """
    ).replace("\n\n", "<br />")

    bokeh.plotting.output_file(html_file_path)
    preamble = bokeh.models.Div(text=preamble_text, height=120)

    def _set_common_bokeh_fig_props(fig):
        fig.toolbar.active_drag = None
        fig.toolbar.active_scroll = None
        fig.toolbar.active_tap = None
        fig.outline_line_color = "#aec6cf"
        fig.outline_line_width = 4
        fig.outline_line_alpha = 0.3
        fig.xaxis.ticker.desired_num_ticks = 15
        fig.xaxis.axis_label = "Date"
        fig.y_range.start = 1
        fig.yaxis.axis_label = "cumulative number of confirmed cases"

    figlog = bokeh.plotting.figure(
        title=f"cumulative COVID-19 case count over time (semi-logarithmic), {shortname}",
        x_axis_type="datetime",
        y_axis_type="log",
        toolbar_location=None,
        background_fill_color="#F2F2F7",
    )
    figlog.scatter(
        "date",
        cname,
        marker="x",
        size=8,
        line_width=3,
        legend_label="raw data",
        source=bokeh.models.ColumnDataSource(data=df_case_data),
    )
    _set_common_bokeh_fig_props(figlog)

    figlog.y_range.bounds = (1, df_case_data[cname].max() * 10)
    figlog.y_range.end = df_case_data[cname].max() * 10
    figlog.line(
        "date",
        "expfit",
        legend_label="exponential fit",
        source=bokeh.models.ColumnDataSource(data=cases_total_fit),
    )

    # figlog.legend.title = "Legend"
    figlog.legend.location = "top_left"

    figlin = bokeh.plotting.figure(
        title=f"cumulative COVID-19 case count over time (linear), {shortname}",
        x_axis_type="datetime",
        toolbar_location=None,
        background_fill_color="#F2F2F7",
    )
    figlin.scatter(
        "date",
        cname,
        marker="x",
        size=8,
        line_width=3,
        legend_label="raw data",
        source=bokeh.models.ColumnDataSource(data=df_case_data),
    )
    _set_common_bokeh_fig_props(figlin)

    figlin.y_range.end = df_case_data[cname].max() * 1.3
    figlin.line(
        "date",
        "expfit",
        legend_label="exponential fit",
        source=bokeh.models.ColumnDataSource(data=cases_total_fit),
    )
    figlin.legend.location = "top_left"

    bokeh.plotting.save(
        column(preamble, figlog, figlin, sizing_mode="stretch_both", max_width=900),
        browser="firefox",
    )
    log.info("wrote %s", html_file_path)


def expfit(df, cname, fit_start, fit_end):
    def _df_to_timedeltas(_df):
        ts = np.array(_df.index.to_pydatetime(), dtype=np.datetime64)

        # Forget absolute time since epoch, we care about the relative time
        # between data points. Get these time differences as native
        # numpy.timedelta64 data points.
        time_deltas = ts - ts.min()

        # Most likely `time_deltas` have microsecond precision,
        # but we do not need to care about that. Use this normalization trick
        # to turn these time deltas into floats:
        # https://stackoverflow.com/a/14921192/145400
        time_deltas_seconds = time_deltas / np.timedelta64(1, "s")
        time_delta_days = time_deltas_seconds / 86400.0
        log.info("time deltas [days]: %s", time_delta_days)
        return time_delta_days

    # Goal: Get day-representing time values as numpy array containing float
    # data type. First, get timestamps as numpy.datetime64 values from pandas
    # dataframe.

    # Create a dataframe with the index time window over which we'd like to
    # draw the fit function
    df_fit = df[fit_start:].copy()

    # Choose a sub time window in the original data set.
    # start 2020-03-10 (pragmatic solution to 0 case count for some states and our
    # goal to build logarithm here), and end March 21 because we clearly don't
    # have an exponential curve and this is to indicate that we don't.

    df = df[fit_start:fit_end]

    # Method: exponential fit by doing a linear fit to natural logarithm of
    # data values.
    time_delta_days = _df_to_timedeltas(df)
    ln_values = np.log(df[cname].to_numpy())
    log.info("time [days] for fit: %s", time_delta_days)
    log.info("ln values/count for fit: %s", ln_values)

    # Function for simple linear regression.
    def linfunc(x, a, b):
        return a + x * b

    # Perform the fit.
    popt, pcov = scipy.optimize.curve_fit(linfunc, time_delta_days, ln_values)
    # log.info("fit paramters: %s, %s", popt, pcov)
    log.info("In `count(days) = a*e^(b*days)` b was found as %.3f", popt[1])

    doubling_time_days = np.log(2) / popt[1]
    log.info("Doubling time: ln(2)/ln(b): %.1f days", doubling_time_days)

    # Get data values from fit function, generate corresponding fit values by
    # inverting logarithm.
    fit_ys_log = linfunc(_df_to_timedeltas(df_fit), *popt)
    fit_ys = np.exp(fit_ys_log)

    # Create a data frame with the original time values as index, and the
    # values from the fit as a series named `expfit`
    df_fit["expfit"] = fit_ys
    return df_fit, doubling_time_days


if __name__ == "__main__":
    main()
