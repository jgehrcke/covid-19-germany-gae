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

    df = fetch_current_csv_as_df()
    for state_isoname in STATE_ISONAME_NAME_MAP:
        generate_plot_html_file(df, state_isoname)
        sys.exit()


def generate_plot_html_file(df_case_data, state_isoname):
    log.info("generate plot for %s", state_isoname)
    statename = STATE_ISONAME_NAME_MAP[state_isoname]
    now = datetime.utcnow()
    cname = state_isoname + "_cases"
    html_file_path = f"plot-{state_isoname}.html"

    preamble_text = dedent(
        f"""
    <h2>Confirmed COVID-19 cases for {statename}, over time</h2>

    Data sources: Gesundheitsministerien (aggregated by RKI, ZEIT ONLINE)

    Background information and code: <a href="https://github.com/jgehrcke/covid-19-germany-gae">github.com/jgehrcke/covid-19-germany-gae</a>

    Author: <a href="https://gehrcke.de">Dr. Jan-Philip Gehrcke</a>

    Data points from before March 10, 2020 are ignored.

    Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}

    Last case count: {df_case_data[cname][-1]} ({df_case_data.index[-1].strftime("%Y-%m-%d")})
    """
    ).replace("\n\n", "<br />")

    bokeh.plotting.output_file(html_file_path)
    preamble = bokeh.models.Div(text=preamble_text, height=120)

    cases_total_fit = expfit(df_case_data, cname)

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

    figlog = bokeh.plotting.figure(
        title="evolution of total case count (half-logarithmic)",
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
    figlog.yaxis.axis_label = "total number of confirmed cases"
    figlog.line(
        "date",
        "expfit",
        legend_label="exponential fit",
        source=bokeh.models.ColumnDataSource(data=cases_total_fit),
    )

    # figlog.legend.title = "Legend"
    figlog.legend.location = "top_left"

    figlin = bokeh.plotting.figure(
        title="evolution of total case count (linear)",
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
    figlin.yaxis.axis_label = "total number of confirmed cases"
    figlin.line(
        "date",
        "expfit",
        legend_label="exponential fit",
        source=bokeh.models.ColumnDataSource(data=cases_total_fit),
    )
    figlin.legend.location = "top_left"

    bokeh.plotting.show(
        column(preamble, figlog, figlin, sizing_mode="stretch_both", max_width=900),
        browser="firefox",
    )


def expfit(df, cname):

    # Parameterize a simple linear function.
    def linfunc(x, a, b):
        return a + x * b

    # Get date-representing x values as numpy array containing float data type.
    x = np.array(df.index.to_pydatetime(), dtype=np.datetime64).astype("float")

    minx = x.min()

    # For the fit don't deal with crazy large x values, transform to time
    # deltas (by substracting mininum), and also transform from nanoseconds
    # seconds.
    fitx = (x - minx) / (10 ** 9 * 86400)

    # Get natural logarithm of data values
    y = np.log(df[cname].to_numpy())
    # log.info(fitx)
    # log.info(y)
    # log.info(", ".join("{%s, %s}" % (x, y) for x, y in zip(fitx, y)))

    # Choose starting parameters for iterative fit.
    p0 = [minx, 3]

    popt, pcov = scipy.optimize.curve_fit(linfunc, fitx, y, p0=p0)
    log.info("fit paramters: %s, %s", popt, pcov)

    # Get data values from fit for the time values corresponding to the time
    # values in the original time series used for fitting.
    fit_ys_log = linfunc(fitx, *popt)

    # Generate corresponding fit values by inverting logarithm.
    fit_ys = np.exp(fit_ys_log)

    # Create a data frame with the original time values as index, and the
    # values from the fit as a series named `expfit`
    df_fit = df.copy()
    df_fit["expfit"] = fit_ys
    return df_fit


def fetch_current_csv_as_df():

    url = "https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/data.csv"
    log.info("fetch csv data from github: %s", url)
    resp = requests.get(url)
    resp.raise_for_status()

    # Parse iso 8601 timestrings into a native DateTimeIndex
    df = pd.read_csv(
        "data.csv", index_col=["time_iso8601"], parse_dates=["time_iso8601"]
    )
    df.index.name = "date"
    return df


if __name__ == "__main__":
    main()
